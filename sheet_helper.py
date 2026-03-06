import gspread
from google.oauth2.service_account import Credentials
import os
from dotenv import load_dotenv
import pandas as pd
from datetime import datetime

load_dotenv()

class SheetManager:
    def __init__(self):
        self.sheet_id = os.getenv('SHEET_ID')
        self.client = None
        self.connect()
    
    def connect(self):
        """Kết nối đến Google Sheet"""
        try:
            # Sử dụng file credentials.json đã download
            creds = Credentials.from_service_account_file(
                'credentials.json',
                scopes=['https://www.googleapis.com/auth/spreadsheets',
                       'https://www.googleapis.com/auth/drive']
            )
            self.client = gspread.authorize(creds)
            self.sheet = self.client.open_by_key(self.sheet_id)
            print("✅ Kết nối Google Sheet thành công!")
        except Exception as e:
            print(f"❌ Lỗi kết nối: {e}")
    
    def get_rates(self, route=None, pol=None, pod=None):
        """Lấy bảng giá từ sheet RATES"""
        try:
            worksheet = self.sheet.worksheet("RATES")
            data = worksheet.get_all_records()
            df = pd.DataFrame(data)
            
            # Filter theo điều kiện
            if pol:
                df = df[df['POL'].str.contains(pol, case=False, na=False)]
            if pod:
                df = df[df['POD'].str.contains(pod, case=False, na=False)]
            if route:
                df = df[df['Route'].str.contains(route, case=False, na=False)]
            
            return df.to_dict('records')
        except Exception as e:
            print(f"Lỗi đọc rates: {e}")
            return []
    
    def get_space(self, pod=None, days=7):
        """Lấy space còn trống"""
        try:
            worksheet = self.sheet.worksheet("SPACE")
            data = worksheet.get_all_records()
            df = pd.DataFrame(data)
            
            # Filter POD nếu có
            if pod:
                df = df[df['POD'].str.contains(pod, case=False, na=False)]
            
            # Lọc theo ETD sắp tới
            # TODO: Thêm logic lọc ngày
            
            return df.to_dict('records')
        except Exception as e:
            print(f"Lỗi đọc space: {e}")
            return []
    
    def get_config(self, key):
        """Lấy config từ sheet CONFIG"""
        try:
            worksheet = self.sheet.worksheet("CONFIG")
            records = worksheet.get_all_records()
            for row in records:
                if row['Key'] == key:
                    return row['Value']
            return None
        except Exception as e:
            print(f"Lỗi đọc config: {e}")
            return None
    
    def update_from_excel(self, file_path, sheet_type="RATES"):
        """Update dữ liệu từ file Excel lên Google Sheet"""
        try:
            # Đọc file Excel
            df = pd.read_excel(file_path)
            
            # Lấy worksheet tương ứng
            worksheet = self.sheet.worksheet(sheet_type)
            
            # Clear dữ liệu cũ (giữ header)
            worksheet.batch_clear(['A2:Z1000'])
            
            # Update dữ liệu mới
            if not df.empty:
                data = df.values.tolist()
                worksheet.append_rows(data, value_input_option='USER_ENTERED')
            
            # Ghi log
            self.log_action("admin", "UPDATE", file_path, "SUCCESS")
            
            return True, f"Đã update {len(df)} dòng lên sheet {sheet_type}"
        except Exception as e:
            self.log_action("admin", "UPDATE", file_path, f"ERROR: {e}")
            return False, str(e)
    
    def log_action(self, user_id, action, query, result):
        """Ghi log vào sheet LOG"""
        try:
            worksheet = self.sheet.worksheet("LOG")
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            worksheet.append_row([timestamp, user_id, action, query, result])
        except:
            pass

# Tạo instance global
sheet_manager = SheetManager()