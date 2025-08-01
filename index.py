from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Literal
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
import os

app = FastAPI()

# MongoDB Setup
MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017")
client = AsyncIOMotorClient(MONGO_URL)
db = client.leave_management

# ---------------------- MODELS ----------------------

class Employee(BaseModel):
    emp_id: str
    name: str
    email: str
    address: str


class LeaveType(BaseModel):
    leave_id : str
    leave_type: str  # e.g. "casual", "medical"


class LeaveApplication(BaseModel):
    emp_id: str
    leave_id: str
    start_date: datetime
    end_date: datetime
    reason: Optional[str] = None
    status: Literal["pending", "approved", "rejected"] = "pending"


# ---------------------- EMPLOYEE APIs ----------------------

@app.post("/employee")
async def add_employee(emp: Employee):
    if await db.employees.find_one({"emp_id": emp.emp_id}):
        raise HTTPException(status_code=400, detail="Employee already exists")
    await db.employees.insert_one(emp.dict())
    return {"success": True, "message": "Employee added successfully"}


@app.get("/employee/{emp_id}")
async def get_employee(emp_id: str):
    emp = await db.employees.find_one({"emp_id": emp_id})
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")
    emp["_id"] = str(emp["_id"])
    return emp


@app.get("/employees")
async def get_all_employees():
    employees = []
    async for emp in db.employees.find():
        emp["_id"] = str(emp["_id"])
        employees.append(emp)
    return employees


# ---------------------- LEAVE TYPE APIs ----------------------

@app.post("/leave_type")
async def add_leave_type(lt: LeaveType):
    if await db.leave_types.find_one({"leave_type": lt.leave_type}):
        raise HTTPException(status_code=400, detail="Leave type already exists")
    await db.leave_types.insert_one(lt.dict())
    return {"success": True, "message": "Leave type added successfully"}


@app.get("/leave_types")
async def get_all_leave_types():
    types = []
    async for lt in db.leave_types.find():
        lt["_id"] = str(lt["_id"])
        types.append(lt)
    return types


# ---------------------- LEAVE APPLICATION APIs ----------------------

@app.post("/apply_leave")
async def apply_leave(req: LeaveApplication):
    # Validate emp_id and leave_type
    emp = await db.employees.find_one({"emp_id": req.emp_id})
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")
    lt = await db.leave_types.find_one({"leave_id": req.leave_id})
    if not lt:
        raise HTTPException(status_code=404, detail="Leave type not found")

    await db.leaves.insert_one(req.dict())
    return {"success": True, "message": "Leave request submitted"}


@app.get("/leaves/{emp_id}")
async def get_leaves_by_emp(emp_id: str):
    leaves = []
    async for leave in db.leaves.find({"emp_id": emp_id}):
        leave["_id"] = str(leave["_id"])
        leaves.append(leave)
    return leaves


@app.get("/all_leaves")
async def get_all_leaves():
    leaves = []
    async for leave in db.leaves.find():
        leave["_id"] = str(leave["_id"])
        leaves.append(leave)
    return leaves


@app.put("/update_leave_status/{leave_id}")
async def update_leave_status(leave_id: str, status: Literal["pending", "approved", "rejected"]):
    result = await db.leaves.update_one(
        {"_id": ObjectId(leave_id)},
        {"$set": {"status": status}}
    )
    return {
        "success": result.modified_count > 0,
        "message": "Status updated" if result.modified_count > 0 else "No changes made"
    }
    
@app.delete("/delete_leave")
async def delete_leave(leave_id: str):
    result = await db.leaves.delete_one({"_id": ObjectId(leave_id)})
    return {
        "success": result.deleted_count > 0,
        "message":"Leave deleted successfully"
            }
                
