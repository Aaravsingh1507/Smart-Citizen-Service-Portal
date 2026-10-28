"""GUI Application"""
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
from datetime import datetime
from queue import Queue

class SmartCitizenApp:
    def __init__(self, root, services):
        self.root = root
        self.services = services
        self.update_queue = Queue()
        self.root.title("Smart Citizen Service Portal - OS Project")
        self.root.geometry("1100x700")
        self.root.minsize(900, 600)
        
        # Style
        style = ttk.Style()
        style.theme_use('clam')
        
        # Create layout
        self.create_sidebar()
        self.create_main_area()
        self.show_dashboard()
        self.start_updates()
    
    def create_sidebar(self):
        sidebar = tk.Frame(self.root, bg='#2c3e50', width=220)
        sidebar.pack(side=tk.LEFT, fill=tk.Y)
        sidebar.pack_propagate(False)
        
        title = tk.Label(sidebar, text="SCSP", bg='#2c3e50', fg='white', 
                        font=('Arial', 18, 'bold'), pady=20)
        title.pack()
        
        buttons = [
            ("Dashboard", self.show_dashboard),
            ("Register Complaint", self.show_register),
            ("Manage Complaints", self.show_manage),
            ("Departments", self.show_departments),
            ("Shared Resources", self.show_resources),
            ("Processing Queue", self.show_queue),
            ("OS Control Center", self.show_os_control),
            ("Audit Logs", self.show_audit),
            ("Reports & Export", self.show_reports),
            ("Settings", self.show_settings),
        ]
        
        for text, cmd in buttons:
            btn = tk.Button(sidebar, text=text, command=cmd, bg='#34495e', fg='white',
                          bd=0, padx=20, pady=10, anchor='w', cursor='hand2')
            btn.pack(fill=tk.X, padx=10, pady=2)
    
    def create_main_area(self):
        self.main_frame = tk.Frame(self.root, bg='#ecf0f1')
        self.main_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        self.content_frame = tk.Frame(self.main_frame, bg='white')
        self.content_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    def clear_content(self):
        for widget in self.content_frame.winfo_children():
            widget.destroy()
    
    def show_dashboard(self):
        self.clear_content()
        tk.Label(self.content_frame, text="Dashboard", font=('Arial', 16, 'bold'), 
                bg='white').pack(anchor='w', padx=10, pady=10)
        
        # Stats frame
        stats_frame = tk.Frame(self.content_frame, bg='white')
        stats_frame.pack(fill=tk.X, padx=10)
        
        try:
            stats = self.services['complaint_service'].get_dashboard_stats()
            worker_status = self.services['complaint_service'].get_worker_status()
            
            cards = [
                ("Total", stats.get('total',0), '#3498db'),
                ("Pending", stats.get('pending',0), '#f39c12'),
                ("Processing", stats.get('processing',0), '#e74c3c'),
                ("Completed", stats.get('completed',0), '#2ecc71'),
                ("Failed", stats.get('failed',0), '#95a5a6'),
            ]
            
            for i, (label, val, color) in enumerate(cards):
                card = tk.Frame(stats_frame, bg=color, width=150, height=80)
                card.pack(side=tk.LEFT, padx=5)
                card.pack_propagate(False)
                tk.Label(card, text=str(val), bg=color, fg='white', 
                        font=('Arial', 24, 'bold')).pack(pady=(10,0))
                tk.Label(card, text=label, bg=color, fg='white').pack()
        except Exception as e:
            tk.Label(self.content_frame, text=f"Error loading stats: {e}", 
                    bg='white', fg='red').pack()
        
        # Operations panel
        ops_frame = tk.LabelFrame(self.content_frame, text="Operations Panel - Real-time", 
                                 bg='white', font=('Arial', 10, 'bold'))
        ops_frame.pack(fill=tk.X, padx=10, pady=20)
        
        try:
            ws = self.services['complaint_service'].get_worker_status()
            qlen = self.services['complaint_service'].get_queue_length()
            info = f"Workers: {len(ws['workers'])} | Queue Length: {qlen}/{ws['queue_max']} | Submitted: {ws['total_submitted']}"
            tk.Label(ops_frame, text=info, bg='white').pack(anchor='w', padx=10, pady=5)
            for w in ws['workers']:
                tk.Label(ops_frame, text=f"  Worker {w['id']}: {w['status']} (✓{w['completed']} ✗{w['failed']})", 
                        bg='white').pack(anchor='w', padx=10)
        except:
            pass
    
    def show_register(self):
        self.clear_content()
        tk.Label(self.content_frame, text="Register Complaint", font=('Arial', 16, 'bold'), 
                bg='white').pack(anchor='w', padx=10, pady=10)
        
        form = tk.Frame(self.content_frame, bg='white')
        form.pack(fill=tk.X, padx=10)
        
        fields = []
        def add_field(label):
            tk.Label(form, text=label, bg='white').pack(anchor='w')
            entry = tk.Entry(form, width=50)
            entry.pack(anchor='w', pady=2)
            fields.append(entry)
            return entry
        
        name = add_field("Citizen Name:")
        phone = add_field("Phone:")
        title = add_field("Complaint Title:")
        location = add_field("Location:")
        cat_var = tk.StringVar(value="General municipal services")
        tk.Label(form, text="Category:", bg='white').pack(anchor='w')
        ttk.Combobox(form, textvariable=cat_var, width=47, 
                    values=["Water supply","Electricity","Roads","Sanitation","Waste collection",
                           "Drainage","Streetlights","Public infrastructure","General municipal services"]).pack(anchor='w')
        tk.Label(form, text="Description:", bg='white').pack(anchor='w')
        desc = tk.Text(form, width=50, height=5)
        desc.pack(anchor='w')
        pri_var = tk.StringVar(value="MEDIUM")
        tk.Label(form, text="Priority:", bg='white').pack(anchor='w')
        ttk.Combobox(form, textvariable=pri_var, width=47, values=["LOW","MEDIUM","HIGH"]).pack(anchor='w')
        
        def submit():
            try:
                cid = self.services['complaint_service'].submit_complaint(
                    name.get(), phone.get(), cat_var.get(), title.get(), 
                    desc.get('1.0', 'end-1c'), location.get(), pri_var.get()
                )
                messagebox.showinfo("Success", f"Complaint registered!\nComplaint ID: {cid}")
                name.delete(0, tk.END); phone.delete(0, tk.END); title.delete(0, tk.END)
                location.delete(0, tk.END); desc.delete('1.0', tk.END)
            except Exception as e:
                messagebox.showerror("Error", str(e))
        
        tk.Button(form, text="Submit Complaint", command=submit, bg='#2ecc71', 
                 fg='white', padx=20, pady=5).pack(anchor='w', pady=10)
    
    def show_manage(self):
        self.clear_content()
        tk.Label(self.content_frame, text="Manage Complaints", font=('Arial', 16, 'bold'), 
                bg='white').pack(anchor='w', padx=10, pady=10)
        try:
            complaints = self.services['complaint_repo'].list_complaints()
            tree = ttk.Treeview(self.content_frame, columns=('ID','Citizen','Category','Title','Status','Priority'), show='headings')
            for col in ('ID','Citizen','Category','Title','Status','Priority'):
                tree.heading(col, text=col)
                tree.column(col, width=100)
            tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            for c in complaints:
                tree.insert('', tk.END, values=(c['id'], c.get('citizen_name',''), c['category'], 
                                               c['title'][:30], c['status'], c['priority']))
        except Exception as e:
            tk.Label(self.content_frame, text=str(e), bg='white').pack()
    
    def show_departments(self):
        self.clear_content()
        tk.Label(self.content_frame, text="Departments", font=('Arial', 16, 'bold'), bg='white').pack(anchor='w', padx=10, pady=10)
        conn = self.services['db'].get_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM departments")
        for r in cur.fetchall():
            tk.Label(self.content_frame, text=f"• {r['name']} - {r['description']}", bg='white').pack(anchor='w', padx=20)
    
    def show_resources(self):
        self.clear_content()
        tk.Label(self.content_frame, text="Shared Resources", font=('Arial', 16, 'bold'), bg='white').pack(anchor='w', padx=10, pady=10)
        try:
            res = self.services['resource_manager'].get_resource_status()
            for r in res:
                tk.Label(self.content_frame, text=f"• {r['name']} ({r['type']}): {r['available']}/{r['total_capacity']} available", 
                        bg='white').pack(anchor='w', padx=20)
        except Exception as e:
            tk.Label(self.content_frame, text=str(e), bg='white').pack()
    
    def show_queue(self):
        self.clear_content()
        tk.Label(self.content_frame, text="Processing Queue", font=('Arial', 16, 'bold'), bg='white').pack(anchor='w', padx=10, pady=10)
        try:
            ws = self.services['complaint_service'].get_worker_status()
            tk.Label(self.content_frame, text=f"Queue Size: {ws['queue_size']} / {ws['queue_max']}", bg='white').pack(anchor='w', padx=10)
        except:
            pass
    
    def show_os_control(self):
        self.clear_content()
        tk.Label(self.content_frame, text="Operating Systems Control Center", font=('Arial', 16, 'bold'), bg='white').pack(anchor='w', padx=10, pady=10)
        info = """OS Concepts Integrated:
• Process & Task Lifecycle (PENDING→CLAIMED→PROCESSING→COMPLETED)
• Multithreading (Worker Pool)
• Producer-Consumer Architecture
• Synchronization (Locks, Transactions)
• Priority Scheduling with Aging
• Deadlock Prevention (Resource Ordering)
• Fault Recovery (Stale Job Detection)
• Resource Management
• Process Management (subprocess)
• File Management (CSV/Reports)"""
        tk.Label(self.content_frame, text=info, bg='white', justify=tk.LEFT).pack(anchor='w', padx=20, pady=10)
    
    def show_audit(self):
        self.clear_content()
        tk.Label(self.content_frame, text="Audit Logs", font=('Arial', 16, 'bold'), bg='white').pack(anchor='w', padx=10, pady=10)
        try:
            events = self.services['audit_service'].get_events(50)
            tree = ttk.Treeview(self.content_frame, columns=('Time','Type','Actor','Details'), show='headings')
            for col in ('Time','Type','Actor','Details'):
                tree.heading(col, text=col)
            tree.column('Details', width=400)
            tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            for e in events:
                tree.insert('', tk.END, values=(e['created_at'], e['event_type'], e['actor'], e['details'][:60]))
        except:
            pass
    
    def show_reports(self):
        self.clear_content()
        tk.Label(self.content_frame, text="Reports and CSV Export", font=('Arial', 16, 'bold'), bg='white').pack(anchor='w', padx=10, pady=10)
        def export():
            try:
                path = self.services['report_service'].export_complaints_csv()
                messagebox.showinfo("Exported", f"Exported to:\n{path}")
            except Exception as e:
                messagebox.showerror("Error", str(e))
        tk.Button(self.content_frame, text="Export Complaints to CSV", command=export, 
                 bg='#3498db', fg='white', padx=20, pady=5).pack(anchor='w', padx=10)
        def summary():
            try:
                rep = self.services['report_service'].generate_summary_report()
                msg = "\n".join([f"{k}: {v}" for k,v in rep.items()])
                messagebox.showinfo("Summary Report", msg)
            except Exception as e:
                messagebox.showerror("Error", str(e))
        tk.Button(self.content_frame, text="Generate Summary Report", command=summary, 
                 bg='#9b59b6', fg='white', padx=20, pady=5).pack(anchor='w', padx=10, pady=5)
    
    def show_settings(self):
        self.clear_content()
        tk.Label(self.content_frame, text="Settings", font=('Arial', 16, 'bold'), bg='white').pack(anchor='w', padx=10, pady=10)
        tk.Label(self.content_frame, text="Database and application configuration", bg='white').pack(anchor='w', padx=10)
    
    def start_updates(self):
        self.root.after(2000, self.periodic_update)
    
    def periodic_update(self):
        # Update UI from main thread
        self.root.after(2000, self.periodic_update)

def run_app(services):
    root = tk.Tk()
    app = SmartCitizenApp(root, services)
    root.mainloop()
