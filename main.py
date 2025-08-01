# ============================
# ✅ main.py (FastAPI + Mongo + MCP)
# ============================

from fastapi import FastAPI, HTTPException
# from fastmcp.ext.fastapi import MCPApp
from fastmcp import FastMCP
from pydantic import BaseModel
from typing import Optional
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
from datetime import datetime, timedelta


app = FastAPI()
# mcp = FastMCP(app)

# MongoDB connection
client = AsyncIOMotorClient("mongodb://localhost:27017")
db = client["leave_db"]
collection = db["leaves"]

class LeaveRequest(BaseModel):
    emp_id: str
    start_date: datetime
    end_date: datetime
    reason: Optional[str] = None
    status: Optional[str] = "pending"
    

class UpdateLeaveRequest(BaseModel):
    emp_id: str
    reason: str

@app.get("/")
async def read_root():
    return {"message": "Server is working!"}

@app.get("/employees")
async def get_employees():
    employees = await collection.find({}).to_list(100)
    return employees

@app.post("/apply_leave")
async def apply_leave(req: LeaveRequest):
    data = req.dict()
    result = await collection.insert_one(data)
    return {"success": True, "leave_id": str(result.inserted_id)}

@app.get("/get_leave")
async def get_leave(emp_id: Optional[str] = None):
    query = {"emp_id": emp_id} if emp_id else {}
    results = await collection.find(query).to_list(100)
    for r in results:
        r["_id"] = str(r["_id"])
    return results

@app.delete("/delete_leave")
async def delete_leave(leave_id: str):
    result = await collection.delete_one({"_id": ObjectId(leave_id)})
    return {"success": result.deleted_count > 0}

@app.put("/approve_leave/{leave_id}")
async def approve_leave(leave_id: str):
    result = await collection.update_one(
        {"_id": ObjectId(leave_id)},
        {"$set": {"status": "approved"}}
    )
    if result.modified_count == 1:
        return {"message": "Leave approved successfully"}
    else:
        return {"message": "Leave not found or already approved"}


@app.get("/leave_balance")
async def leave_balance(emp_id: str):
    total_leaves = 30
    # Fetch all approved leaves of that employee
    leave_requests = await collection.find({"emp_id": emp_id, "status": "approved"}).to_list(None)

    used_days = 0
    for leave in leave_requests:
        start = leave["start_date"]
        end = leave["end_date"]
        days = (end - start).days + 1  # include end date
        used_days += days

    return {
        "emp_id": emp_id,
        "total_leaves": total_leaves,
        "used_leaves": used_days,
        "balance": total_leaves - used_days
    }



@app.put("/update_leave_by_emp")
async def update_leave_by_emp(req: UpdateLeaveRequest):
    result = await collection.update_one(
        {"emp_id": req.emp_id},
        {"$set": {"reason": req.reason}}
    )

    return {
        "success": result.modified_count > 0,
        "message": "Leave reason updated." if result.modified_count > 0 else "No changes made."
    }



# Run using: uvicorn main:app --reload
