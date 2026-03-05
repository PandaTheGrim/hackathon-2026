db = db.getSiblingDB("checker");

db.createCollection("results");
db.createCollection("tasks");
db.createCollection("prompts");
db.createCollection("submissions");

db.results.createIndex({task_id: 1});
db.results.createIndex({created_at: -1});
db.results.createIndex({candidate_id: 1});