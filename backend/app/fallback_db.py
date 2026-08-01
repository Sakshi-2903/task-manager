import re
from copy import deepcopy
from datetime import datetime, timezone


class _Cursor(list):
    def sort(self, key_or_list, direction=None):
        if isinstance(key_or_list, list):
            sort_keys = key_or_list
        else:
            sort_keys = [(key_or_list, direction)]
        for field, direc in reversed(sort_keys):
            self[:] = sorted(
                self,
                key=lambda doc, f=field: doc.get(f, datetime.min.replace(tzinfo=timezone.utc)),
                reverse=direc == -1,
            )
        return self

    def skip(self, count):
        self[:] = self[count:] if count < len(self) else []
        return self

    def limit(self, count):
        self[:] = self[:count]
        return self


class FallbackCollection:
    def __init__(self):
        self._docs = {}

    def create_index(self, *args, **kwargs):
        return None

    def find(self, query=None):
        query = query or {}
        docs = [deepcopy(doc) for doc in self._docs.values() if self._matches(query, doc)]
        return _Cursor(docs)

    def count_documents(self, query=None):
        return len(self.find(query))

    def insert_one(self, document):
        doc = deepcopy(document)
        doc.setdefault("_id", object())
        self._docs[doc["_id"]] = doc
        return type("Result", (), {"inserted_id": doc["_id"]})()

    def find_one(self, query):
        for doc in self._docs.values():
            if self._matches(query, doc):
                return deepcopy(doc)
        return None

    def find_one_and_update(self, query, update, return_document=None):
        for doc in self._docs.values():
            if self._matches(query, doc):
                updated = deepcopy(doc)
                for key, value in update.get("$set", {}).items():
                    updated[key] = value
                self._docs[doc["_id"]] = updated
                return deepcopy(updated)
        return None

    def delete_one(self, query):
        for doc_id, doc in list(self._docs.items()):
            if self._matches(query, doc):
                del self._docs[doc_id]
                return type("Result", (), {"deleted_count": 1})()
        return type("Result", (), {"deleted_count": 0})()

    def _matches(self, query, doc):
        if not query:
            return True
        for key, value in query.items():
            if key == "status" and doc.get("status") != value:
                return False
            if key == "title":
                if isinstance(value, dict):
                    regex = value.get("$regex")
                    flags = value.get("$options", "")
                    if regex and not re.search(regex, doc.get("title", ""), flags=re.I if "i" in flags else 0):
                        return False
                elif doc.get("title") != value:
                    return False
            elif doc.get(key) != value:
                return False
        return True


class FallbackDatabase:
    def __init__(self):
        self.tasks = FallbackCollection()

    def command(self, name):
        return {"ok": 1}
