from concurrent import futures
import grpc
import pandas as pd
import inventory_pb2
import inventory_pb2_grpc
import numpy as np
import math

class InventoryServiceServicer(inventory_pb2_grpc.InventoryServiceServicer):
    def __init__(self, excel_file_path):
        self.excel_file_path = excel_file_path
        self.inventory_data = self.load_inventory_data()

    def load_inventory_data(self):
        df = pd.read_excel(self.excel_file_path)
        return df.to_dict(orient='records')

    def searchByID(self, request, context):
        inventory_id = request.id

        # Search for the Inventory ID in the local data
        found_inventory = next((item for item in self.inventory_data if item['Inventory_ID'] == inventory_id), None)

        if found_inventory:
            # Convert the found inventory data to an InventoryRecord message
            discontinued_value = found_inventory.get('Discontinued')

            # Check if the Discontinued value is None or an empty string
            if discontinued_value is None or str(discontinued_value).strip() == "":
                discontinued_bool = False  # Set to False for empty values
            else:
                # Check if the Discontinued value is a number (float)
                if isinstance(discontinued_value, (int, float)):
                    discontinued_bool = bool(discontinued_value)
                else:
                    # Check if the Discontinued value is "yes"
                    if str(discontinued_value).strip().lower() == "yes":
                        discontinued_bool = True
                    else:
                        try:
                            # Check if the Discontinued value is NaN
                            discontinued_bool = math.isnan(float(discontinued_value))
                        except (TypeError, ValueError):
                            # If it's not a number or cannot be converted to NaN, set to False
                            discontinued_bool = False

            return inventory_pb2.InventoryRecord(
                Inventory_ID=str(found_inventory['Inventory_ID']),
                Name=found_inventory['Name'],
                Description=found_inventory['Description'],
                Price=float(found_inventory['Price']),
                Quantity_in_Stock=int(found_inventory['Quantity_in_Stock']),
                Quantity_in_Reorder=int(found_inventory['Quantity_in_Reorder']),
                Discontinued=discontinued_bool
            )
        else:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details(f"Inventory ID '{inventory_id}' not found.")
            return inventory_pb2.InventoryRecord()  # Return an empty InventoryRecord

    def searchFullRowByID(self, request, context):
        inventory_id = request.id

        # Search for the Inventory ID in the local data
        found_inventory = next((item for item in self.inventory_data if item['Inventory_ID'] == inventory_id), None)

        if found_inventory:
            # Return the entire row of data for the found inventory as a dictionary
            return {
                'Inventory_ID': str(found_inventory['Inventory_ID']),
                'Name': found_inventory['Name'],
                'Description': found_inventory['Description'],
                'Price': float(found_inventory['Price']),
                'Quantity_in_Stock': int(found_inventory['Quantity_in_Stock']),
                'Quantity_in_Reorder': int(found_inventory['Quantity_in_Reorder']),
                'Discontinued': bool(found_inventory['Discontinued'])
            }
        else:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details(f"Inventory ID '{inventory_id}' not found.")
            return {}  # Return an empty dictionary

    def search(self, request, context):
        key_name = request.key_name
        key_value = str(request.key_value).lstrip('$')  # Convert to string and remove dollar sign

        # Search for the key and value in the local data
        found_inventory = next(
            (item for item in self.inventory_data if str(item.get(key_name)).lstrip('$') == key_value), None)

        if found_inventory:
            # Convert the found inventory data to an InventoryRecord message
            return inventory_pb2.InventoryRecord(
                Inventory_ID=str(found_inventory['Inventory_ID']),
                Name=found_inventory['Name'],
                Description=found_inventory['Description'],
                Price=float(found_inventory['Price']),
                Quantity_in_Stock=int(found_inventory['Quantity_in_Stock']),
                Quantity_in_Reorder=int(found_inventory['Quantity_in_Reorder']),
                Discontinued=bool(found_inventory['Discontinued']) if 'Discontinued' in found_inventory else False
            )
        else:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details(f"Key '{key_name}' with value '{key_value}' not found.")
            return inventory_pb2.InventoryRecord()  # Return an empty InventoryRecord

    def searchRange(self, request, context):
        key_name = request.key_name
        key_value_start = request.key_value_start
        key_value_end = request.key_value_end

        # Convert key values to float for numeric comparisons
        key_value_start = float(key_value_start)
        key_value_end = float(key_value_end)

        # Search for the key within the specified range in the local data
        matching_inventory = [
            item for item in self.inventory_data
            if key_name in item and
               isinstance(item[key_name], (int, float)) and
               key_value_start <= float(item[key_name]) <= key_value_end
        ]

        for found_inventory in matching_inventory:
            # Convert the found inventory data to an InventoryRecord message
            yield inventory_pb2.InventoryRecord(
                Inventory_ID=str(found_inventory['Inventory_ID']),
                Name=found_inventory['Name'],
                Description=found_inventory['Description'],
                Price=float(found_inventory['Price']),
                Quantity_in_Stock=int(found_inventory['Quantity_in_Stock']),
                Quantity_in_Reorder=int(found_inventory['Quantity_in_Reorder']),
                Discontinued=bool(found_inventory['Discontinued']) if 'Discontinued' in found_inventory else False
            )

    def getDistribution(self, request, context):
        key_name = request.key_name
        percentile = request.percentile

        # Extract the values for the specified key from the local data
        values = [item.get(key_name, 0) for item in self.inventory_data]

        if not values:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details(f"Key '{key_name}' not found in the inventory data.")
            return inventory_pb2.DistributionResponse(value=None)

        # Calculate the percentile value with numpy.percentile
        result = self.calculate_percentile(values, percentile)

        return inventory_pb2.DistributionResponse(value=result)

    def calculate_percentile(self, values, percentile):
        # Use numpy.percentile for accurate percentile calculation
        result = np.percentile(values, percentile, interpolation='linear')

        return result

    def update(self, request, context):
        key_name = request.key_name
        key_value = request.key_value
        val_name = request.val_name
        val_val_new = request.val_val_new

        # Find the record with the given key name and key value
        record_index = next((index for index, item in enumerate(self.inventory_data)
                             if item.get(key_name) == key_value), None)

        if record_index is not None:
            # Update the specified attribute with the new value
            self.inventory_data[record_index][val_name] = val_val_new

            # Save the updated data back to the Excel file
            self.save_inventory_data()

            return inventory_pb2.UpdateResponse(success=True)
        else:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details(f"Record with '{key_name}'='{key_value}' not found.")
            return inventory_pb2.UpdateResponse(success=False)

    def save_inventory_data(self):
        # Save the updated data back to the Excel file
        updated_df = pd.DataFrame(self.inventory_data)
        updated_df.to_excel(self.excel_file_path, index=False)


def serve():
    excel_file_path = r'InventoryData.xlsx'
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    inventory_service = InventoryServiceServicer(excel_file_path)
    inventory_pb2_grpc.add_InventoryServiceServicer_to_server(inventory_service, server)
    server.add_insecure_port('[::]:50051')  # Bind to port 50051 on all interfaces
    server.start()
    print("gRPC Server is running ............ \n")
    server.wait_for_termination()
    print("gRPC Server terminated !!!")

if __name__ == "__main__":
    serve()