db = db.getSiblingDB("app");

db.createCollection("results");

db.results.createIndex({ task_id: 1 });
db.results.createIndex({ created_at: -1 });