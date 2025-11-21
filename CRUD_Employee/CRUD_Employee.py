import json
import boto3
import decimal

# Kết nối DynamoDB
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('EmployeeTable_20251118')

# -------- Helper functions --------

# Convert float sang Decimal cho DynamoDB
def to_decimal(data):
    return {
        k: decimal.Decimal(str(v)) if isinstance(v, float) else v
        for k, v in data.items()
    }

# Convert Decimal từ DynamoDB sang int/float để JSON serialize được
def decimal_to_native(obj):
    if isinstance(obj, list):
        return [decimal_to_native(i) for i in obj]
    elif isinstance(obj, dict):
        return {k: decimal_to_native(v) for k, v in obj.items()}
    elif isinstance(obj, decimal.Decimal):
        if obj % 1 == 0:
            return int(obj)
        else:
            return float(obj)
    else:
        return obj

# -------- Lambda Handler --------

def lambda_handler(event, context):
    print("Event:", json.dumps(event))
    method = event.get('httpMethod')
    path_params = event.get('pathParameters') or {}
    body = event.get('body')

    # Lấy employee_id từ path hoặc body
    employee_id = path_params.get('employee_id')
    if body:
        try:
            body_data = json.loads(body)
        except Exception:
            body_data = {}
        if not employee_id and 'employee_id' in body_data:
            employee_id = body_data['employee_id']
    else:
        body_data = {}

    # ---------- CREATE ----------
    if method == 'POST':
        if not body_data.get('employee_id'):
            return {'statusCode': 400, 'body': json.dumps({'error': 'employee_id is required'})}

        item = to_decimal(body_data)
        table.put_item(Item=item)

        return {
            'statusCode': 200,
            'body': json.dumps({'message': 'Record created', 'item': body_data})
        }

    # ---------- READ ----------
    elif method == 'GET':
        # Nếu có employee_id => Get 1 record
        if employee_id:
            response = table.get_item(Key={'employee_id': employee_id})
            if 'Item' not in response:
                return {'statusCode': 404, 'body': json.dumps({'error': 'Record not found'})}

            item = decimal_to_native(response['Item'])
            return {'statusCode': 200, 'body': json.dumps(item)}

        # Nếu không có employee_id => Get all records
        else:
            response = table.scan()
            items = response.get('Items', [])
            all_items = decimal_to_native(items)
            return {
                'statusCode': 200,
                'body': json.dumps(all_items)
            }

    # ---------- UPDATE ----------
    elif method == 'PUT':
        if not employee_id:
            return {'statusCode': 400, 'body': json.dumps({'error': 'employee_id is required'})}
        if not body_data:
            return {'statusCode': 400, 'body': json.dumps({'error': 'Missing body data'})}

        update_expression = "SET " + ", ".join(f"#{k}=:{k}" for k in body_data.keys())
        expression_attr_names = {f"#{k}": k for k in body_data.keys()}
        expression_attr_values = {
            f":{k}": decimal.Decimal(str(v)) if isinstance(v, float) else v
            for k, v in body_data.items()
        }

        table.update_item(
            Key={'employee_id': employee_id},
            UpdateExpression=update_expression,
            ExpressionAttributeNames=expression_attr_names,
            ExpressionAttributeValues=expression_attr_values
        )

        return {'statusCode': 200, 'body': json.dumps({'message': 'Record updated'})}

    # ---------- DELETE ----------
    elif method == 'DELETE':
        if not employee_id:
            return {'statusCode': 400, 'body': json.dumps({'error': 'employee_id is required'})}

        table.delete_item(Key={'employee_id': employee_id})
        return {'statusCode': 200, 'body': json.dumps({'message': 'Record deleted'})}

    # ---------- METHOD NOT ALLOWED ----------
    else:
        return {
            'statusCode': 405,
            'body': json.dumps({'error': f'Method {method} not allowed'})
        }
