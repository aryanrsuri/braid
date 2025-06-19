from fastapi import FastAPI
from util.versionstamp import versionid


app = FastAPI()
@app.get("/event/{event_id}")
async def get_event(event_id: versionid, filter: str | None):
    return {
            "event_id": event_id,
            "event_name" : "sample_event",
            "filter": filter
            }
