import boto3
import json
from boto3.dynamodb.conditions import Attr

def lambda_handler(event, context):
    # 1. Lấy query params từ API
    params = event.get("queryStringParameters") or {}
    
    # 2. Lấy tên bảng người dùng truyền vào
    table_name = params.get("table")
    action = params.get("action")
    
    if not table_name:
        return {
            "statusCode": 400,
            "body": json.dumps({"error": "Thiếu query param 'table'!"})
        }
    
    # 3. Kết nối DynamoDB và chọn đúng bảng
    dynamodb = boto3.resource('dynamodb')  
    
    # --------------- Các hàm xử lý dữ liệu cho dashboard ---------------
    def overall_emp_info(): #hàm lấy thông tin nhân viên 
        emp_info_table = dynamodb.Table("employee_info")

        response = emp_info_table.scan()
        items = response.get("Items", [])

        proceed = []

        for emp in items:
            join_date = emp.get("join_date")
            start_year = None 

            if join_date and "/" in join_date:
                try:
                    _,yy = join_date.split("/")
                    start_year = int(yy)
                except :
                    start_year = None
            proceed.append({
                "employee_id": emp.get("employee_id"),
                "team": emp.get("team"),
                "position": emp.get("position"),
                "age": emp.get("age"),
                "gender": emp.get("gender"),
                "join_date": join_date,
                "start_year": start_year
            })

        return proceed
#---------------------------------------------------------------------------
    def team_scoring(): #hàm lấy điểm của nhân viên trong team dùng để vẽ biểu đồ phân phối
        table = dynamodb.Table(table_name)
        team_name = params.get("team_name")
        try:
            response = table.scan(
                ProjectionExpression = "employee_id, final_score, team",
                FilterExpression = Attr("team").eq(team_name)
            )
            items = response.get("Items", [])
            return items
        except Exception as e:
            return {"error": f"Lỗi khi query DynamoDB: {str(e)}"}
#---------------------------------------------------------------------------       
    def emp_individual_info(): #hàm lấy thông tin + chỉ số làm việc của nhân viên, filtering theo lịch sử chấm điểm theo từng quý 
        table = dynamodb.Table(table_name)
        emp_id = params.get("employee_id")
        try: 
            response = table.scan(
                # ProjectionExpression ="emplo",
                FilterExpression = Attr("employee_id").eq(emp_id)
            )
            items = response.get("Items", [])
            return items
        except Exception as e:
            return {"error": f"Lỗi khi query DynamoDB: {str(e)}"}

    # 5. Trả dữ liệu về API
    
    if action == "overall":
        data = overall_emp_info()

    elif action == "team_score":
         data = team_scoring()

    elif action == "individual":
         data = emp_individual_info()

    else:
        data = {"error": "Thiếu query param 'action'!"}

    return {
        "statusCode": 200,
        "body": json.dumps(data, default=str)
    }