import datetime
import json
import os

from bson.objectid import ObjectId
from flask import Flask, request, jsonify
from pymongo import MongoClient

app = Flask(__name__)

# MongoDB setup
client = MongoClient("mongodb://127.0.0.1:27017/")
databaseName = "mydatabase"
db = client[databaseName]
events_collection = db['events']

# Multer setup (for handling file uploads)
UPLOAD_FOLDER = 'uploads/'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)


# Routes
@app.route('/api/v3/app/events', methods=['POST'])
def create_event():
    new_event = {
        'name': request.json['name'],
        'tagline': request.json['tagline'],
        'schedule': request.json['schedule'],
        'description': request.json['description'],
        'moderator': request.json['moderator'],
        'category': request.json['category'],
        'sub_category': request.json['sub_category'],
        'rigor_rank': request.json['rigor_rank'],
        'image': request.files['image'].filename if 'image' in request.files else '',
    }

    event_id = events_collection.insert_one(new_event).inserted_id
    return str(event_id), 200


@app.route('/api/v3/app/events/<string:event_id>', methods=['DELETE'])
def delete_event(event_id):
    result = events_collection.delete_one({'_id': ObjectId(event_id)})

    if result.deleted_count == 1:
        return 'Event deleted successfully', 200
    else:
        return 'Event not found', 404


@app.route('/api/v3/app/events/<string:event_id>', methods=['PUT'])
def update_event(event_id):
    fields_to_update = ['name', 'tagline', 'schedule', 'description', 'moderator', 'category', 'sub_category',
                        'rigor_rank']
    updated_fields = {}

    for field in fields_to_update:
        if field in request.form:
            updated_fields[field] = request.form[field]

    if 'image' in request.files:
        filename = f"{datetime.datetime.now().timestamp()}_{request.files['image'].filename}"
        request.files['image'].save(os.path.join(UPLOAD_FOLDER, filename))
        updated_fields['image'] = filename

    result = events_collection.find_one_and_update(
        {'_id': ObjectId(event_id)},
        {'$set': updated_fields},
        return_document=True
    )

    if result:
        return 'Event updated successfully', 200
    else:
        return 'Event not found', 404


@app.route('/api/v3/app/events/<string:event_id>', methods=['GET'])
def get_event(event_id):
    event = events_collection.find_one({'_id': ObjectId(event_id)})

    if event:
        event['_id'] = str(event['_id'])  # Convert ObjectId to string
        return jsonify(event), 200
    else:
        return 'Event not found', 404


@app.route('/api/v3/app/events', methods=['GET'])
def get_events():
    query = {}
    event_type = request.args.get('type')
    limit = int(request.args.get('limit', 10))
    page = int(request.args.get('page', 1))
    skip = (page - 1) * limit

    if event_type == 'latest':
        current_utc_time = datetime.datetime.utcnow()
        query['schedule'] = {'$lte': current_utc_time.strftime('%Y-%m-%dT%H:%M:%SZ')}
        sort_order = [('schedule', -1)]
    else:
        sort_order = []

    events = events_collection.find(query).sort(sort_order).skip(skip).limit(limit)
    events_list = list(events)
    for event in events_list:
        event['_id'] = str(event['_id'])

    return json.dumps(events_list), 200


if __name__ == '__main__':
    app.run(port=3000)
