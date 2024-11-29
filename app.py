import requests
import re
import sqlite3
import unicodedata
import tkinter as tk
from tkinter import messagebox
from tkinter import scrolledtext 

"""建立資料表結構，若不存在才建立"""
def setup_database()-> None:
    try:
        with sqlite3.connect("contacts.db") as conn:
            cursor = conn.cursor()
            cursor.execute(
                '''CREATE TABLE IF NOT EXISTS contacts (
            iid INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            title TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE
        )'''
            )
            conn.commit()
    except sqlite3.DatabaseError as e:
        print(f"資料庫操作發生錯誤: {e}")
    except Exception as e:
        print(f"發生其它錯誤 {e}")

"""將資料存入資料庫，增加例外處理，如果重複資料跳過"""
def save_to_database(count:int,name_match_list:list,career_match_list:list,unique_emails:list) -> None:
    conn = sqlite3.connect("contacts.db")
    cursor = conn.cursor()
    
    for i in range(count):
        try:
            cursor.execute(
                'INSERT INTO "contacts" (name,title,email) VALUES (?,?,?)',
                (name_match_list[i],career_match_list[i],unique_emails[i])
            )
        except sqlite3.IntegrityError as e:
           continue
    conn.commit()
    

"""列印資料，使用固定寬度格式對齊輸出，可處理中英文對齊"""
def parse_contacts(rows:list,scrolled_text_widget:scrolledtext)->None:
    def get_display_width(text: str) -> int:
        """計算字串的顯示寬度，考慮到全形和半形字元"""
        return sum(2 if unicodedata.east_asian_width(char) in 'WF' else 1 for char in text)

    def pad_to_width(text: str, width: int) -> str:
        """將字串填充到指定的寬度"""
        current_width = get_display_width(text)
        padding = width - current_width
        return text + ' ' * padding
    
     # 每次執行arse_contacts清空 ScrolledText 避免ScrolledText出現多個資料
    scrolled_text_widget.delete("1.0", tk.END)
    headers = ['姓名', '職稱', 'Email']
    widths = [20, 24,30 ]

    #將資料在scrolledtext輸出
    header_line = ''.join(pad_to_width(header, width) for header, width in zip(headers, widths))
    scrolled_text_widget.insert(tk.END, f"{header_line}\n")
    scrolled_text_widget.insert(tk.END, "-" * sum(widths) + "\n")

    
    for row in rows:
        line = ''.join(
            pad_to_width(str(row[key]), width)
            for key, width in zip(['name', 'title', 'email'], widths)
        )
        scrolled_text_widget.insert(tk.END, f"{line}\n")



"""
    在點擊抓取按鈕時執行的動作。
    retun 1代表url為空
    return 0代表可以正常執行
    1. 從使用者輸入的 URL 中抓取網頁資料。
    2. 使用正規表示式提取姓名、職稱和電子郵件。
    3. 將資料存入資料庫並更新顯示。
"""
def on_scrape() ->int:
        setup_database()
        url=url_entry.get().strip()
        #如果網址為空返迴form
        if(url==""):
          messagebox.showinfo("錯誤", "網址不能為空")
          return 1        
        try:
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36'
                        }
            response = requests.get(url,headers=headers)
            response.raise_for_status()
        except requests.exceptions.HTTPError as err:
            messagebox.showerror("網路錯誤", f"無法取得網頁：{err.response.status_code}")
            return 0
        except requests.exceptions.ConnectionError as err:
            messagebox.showerror("網路錯誤", f"無法連接網站：{err}")
            return 0
        else:
            #messagebox.showinfo("成功", f"成功抓取網頁內容，狀態碼：{response.status_code}")

            # 描述 name,career,email 的正規表示式物件 pattern
            email_pattern = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
            name_pattern =re.compile(r'<div class="member_name"><a href="[^"]+">([^<]+)</a>')
            career_pattern = re.compile(r'<div class="member_info_content"[^>]*>([^<]*教授[^<]*)</div>')

            # 從網頁尋找目標，將符合正規表示式的資料，分別建立 list:name、email、tiltle並存入
            name_match_list=name_pattern.findall(response.text)
            email_match_list = email_pattern.findall(response.text)  
            career_match_list=career_pattern.findall(response.text)

            #count紀錄有多少人資料
            count=0
            for name in name_match_list:
                count+=1

            #去除重複資料且把頁尾csie@ncut.edu.tw篩選掉
            unique_emails=[]
            for email in email_match_list:
                if email not in unique_emails and email != 'csie@ncut.edu.tw':
                    unique_emails.append(email)

            # 將抓取的資料存入資料庫
            save_to_database(count,name_match_list,career_match_list,unique_emails)

            #連結資料庫
            conn = sqlite3.connect("contacts.db")
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM contacts")
            columns = [description[0] for description in cursor.description]  # 取得欄位名稱

            # 將查詢結果轉為字典列表
            rows=[]
            for row in cursor.fetchall():
                rows.append( dict(zip(columns, row))) #將每行轉為字典後追加到列表

            parse_contacts(rows,result_text)
            conn.close()
            return 0
            

   
   



form = tk.Tk()                          # 以 tk.TK() 類別建立視窗物件
# 窗相關設定
form.title('聯絡資訊爬蟲')                       # 設定視窗標題
form.geometry('640x480')                # 設定視窗的寬度與高度                   # 視窗寬度與長度可否改變
form.grid_rowconfigure(1,weight=1)
form.grid_columnconfigure(1,weight=1)

Label=tk.Label
url_label = Label(form, text="URL:")
url_label.grid(row=0, column=0, sticky="w", padx=5, pady=5)

Entry=tk.Entry
url_entry = Entry(form, width=50)
url_entry.grid(row=0, column=1, sticky="ew", padx=5, pady=5)



result_text = scrolledtext.ScrolledText(form, wrap="word")
result_text.grid(row=1, column=0, columnspan=3, sticky="nsew",padx=5, pady=5)
Button=tk.Button

scrape_button = Button(form,text="抓取", font=("新細明體",12), command=on_scrape,width=15)
scrape_button.grid(row=0, column=2, padx=10, pady=5)    
form.mainloop()   