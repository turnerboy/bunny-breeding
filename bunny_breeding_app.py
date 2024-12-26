############################################################################
#  LARGE SINGLE-FILE SCRIPT (~1400+ lines) - FULL CODE, NO OMISSIONS
#  With: who is due? = does only, single breeding record displayed,
#  number born/alive in RecordBreedingPage, etc.
############################################################################

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
import os
import json
import uuid
import shutil
import datetime
from datetime import timedelta
from PIL import Image, ImageTk

# For PDF export (lineage)
try:
    from reportlab.lib.pagesizes import landscape, A4
    from reportlab.pdfgen import canvas
    from reportlab.lib.utils import ImageReader
except ImportError:
    pass

DATA_FOLDER = "data"
APP_DATA_FILE = os.path.join(DATA_FOLDER, "app_data.json")
BUNNIES_FOLDER = "bunnies"
TYPES_FILE = os.path.join(DATA_FOLDER, "types.json")

############################################################################
#  UTILITY
############################################################################

def ensure_directories():
    if not os.path.exists(DATA_FOLDER):
        os.makedirs(DATA_FOLDER)
    if not os.path.exists(BUNNIES_FOLDER):
        os.makedirs(BUNNIES_FOLDER)

def load_app_data():
    if not os.path.exists(APP_DATA_FILE):
        return {"bunnies": {}}
    with open(APP_DATA_FILE, "r") as f:
        return json.load(f)

def save_app_data(data):
    with open(APP_DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

def load_types():
    if not os.path.exists(TYPES_FILE):
        return []
    with open(TYPES_FILE, "r") as f:
        return json.load(f)

def save_types(type_list):
    with open(TYPES_FILE, "w") as f:
        json.dump(sorted(set(type_list)), f, indent=4)

def create_bunny_folder(bunny_id):
    folder_path = os.path.join(BUNNIES_FOLDER, bunny_id)
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
    return folder_path

def save_bunny_profile(bunny_id, profile_data):
    folder_path = os.path.join(BUNNIES_FOLDER, bunny_id)
    profile_path = os.path.join(folder_path, "profile.json")
    with open(profile_path, "w") as f:
        json.dump(profile_data, f, indent=4)

def load_bunny_profile(bunny_id):
    profile_path = os.path.join(BUNNIES_FOLDER, bunny_id, "profile.json")
    if not os.path.exists(profile_path):
        return {}
    with open(profile_path, "r") as f:
        return json.load(f)

def compress_and_save_image(src_path, dest_folder, bunny_name):
    from PIL import Image
    clean_name = bunny_name.lower().replace(" ", "_")
    final_filename = f"{clean_name}.jpg"
    final_dest = os.path.join(dest_folder, final_filename)
    try:
        with Image.open(src_path) as img:
            img = img.convert("RGB")
            img.save(final_dest, "JPEG", quality=85)
    except Exception as e:
        print("Error compressing/saving image:", e)
        return ""
    return final_filename

def update_bunny_name_references(old_name, new_name, bunny_id, data):
    """
    If a bunny's name changes, update references in all breeding
    records that mention old_name or bunny_id.
    """
    for b_id, info in data["bunnies"].items():
        bh = info.get("breeding_history", [])
        changed = False
        for rec in bh:
            if rec.get("mom_id") == bunny_id or rec.get("mom_name") == old_name:
                rec["mom_name"] = new_name
                changed = True
            if rec.get("dad_id") == bunny_id or rec.get("dad_name") == old_name:
                rec["dad_name"] = new_name
                changed = True
        if changed:
            data["bunnies"][b_id]["breeding_history"] = bh


############################################################################
#  DATE PICKER
############################################################################
class DatePicker(tk.Toplevel):
    """A small, minimal date picker returning a selected date in YYYY-MM-DD."""
    def __init__(self, parent, initial_date=None):
        super().__init__(parent)
        self.title("Pick Date")
        self.configure(bg="#FAFAFA")
        self.selected_date = None
        self.resizable(False, False)

        if initial_date is None:
            initial_date = datetime.date.today()
        self.current_year = initial_date.year
        self.current_month = initial_date.month

        header_frame = tk.Frame(self, bg="#FAFAFA")
        header_frame.pack(pady=5)
        self.lbl_month_year = tk.Label(header_frame, font=("Helvetica", 10, "bold"), bg="#FAFAFA")
        self.lbl_month_year.pack(side=tk.LEFT, padx=5)

        btn_prev = tk.Button(header_frame, text="<", width=2, command=self.prev_month, bg="#FFF")
        btn_prev.pack(side=tk.LEFT, padx=2)
        btn_next = tk.Button(header_frame, text=">", width=2, command=self.next_month, bg="#FFF")
        btn_next.pack(side=tk.LEFT, padx=2)

        self.days_frame = tk.Frame(self, bg="#FAFAFA")
        self.days_frame.pack(padx=5, pady=5)

        self.draw_calendar()

    def draw_calendar(self):
        for w in self.days_frame.winfo_children():
            w.destroy()

        month_start = datetime.date(self.current_year, self.current_month, 1)
        self.lbl_month_year.config(text=month_start.strftime("%B %Y"))

        start_weekday = month_start.weekday()  # Monday=0, Sunday=6
        next_month = (month_start.replace(day=28) + datetime.timedelta(days=4)).replace(day=1)
        days_in_month = (next_month - datetime.timedelta(days=1)).day

        days_of_week = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        header_row = tk.Frame(self.days_frame, bg="#FAFAFA")
        header_row.pack()
        for d in days_of_week:
            tk.Label(header_row, text=d, width=3, bg="#FAFAFA", fg="blue").pack(side=tk.LEFT, padx=2)

        row_frame = tk.Frame(self.days_frame, bg="#FAFAFA")
        row_frame.pack(pady=2)
        col = 0
        day_num = 1

        # Insert blanks up to start_weekday
        for _ in range(start_weekday):
            tk.Label(row_frame, text="", width=3, bg="#FAFAFA").pack(side=tk.LEFT, padx=2)
            col += 1

        while day_num <= days_in_month:
            if col >= 7:
                row_frame = tk.Frame(self.days_frame, bg="#FAFAFA")
                row_frame.pack()
                col = 0
            btn_day = tk.Button(row_frame, text=str(day_num), width=2, bg="#EEE",
                                command=lambda d=day_num: self.select_date(d))
            btn_day.pack(side=tk.LEFT, padx=2)
            day_num += 1
            col += 1

    def select_date(self, d):
        self.selected_date = datetime.date(self.current_year, self.current_month, d)
        self.destroy()

    def prev_month(self):
        first_day = datetime.date(self.current_year, self.current_month, 1)
        prev_month_last_day = first_day - datetime.timedelta(days=1)
        self.current_year = prev_month_last_day.year
        self.current_month = prev_month_last_day.month
        self.draw_calendar()

    def next_month(self):
        next_month_first_day = (datetime.date(self.current_year, self.current_month, 1)
                                + datetime.timedelta(days=31))
        self.current_year = next_month_first_day.year
        self.current_month = next_month_first_day.month
        self.draw_calendar()

############################################################################
#  BUNNY PROFILE WINDOW
############################################################################
class BunnyProfileWindow(tk.Toplevel):
    """
    A Toplevel window to show/edit a bunny's profile:
     - Basic info
     - Delete bunny
     - Two lists: 'Breeding History' & 'Litter History'
    """
    def __init__(self, parent, bunny_id):
        super().__init__(parent)
        self.title("Bunny Profile")
        self.bunny_id = bunny_id
        self.resizable(False, False)

        data = load_app_data()
        self.bunny = data["bunnies"][bunny_id]

        tk.Label(self, text=f"Bunny Profile: {self.bunny['name']}",
                 font=("Helvetica", 14, "bold")).pack(pady=10)

        info_frame = tk.Frame(self)
        info_frame.pack()

        row = 0
        tk.Label(info_frame, text="Name:").grid(row=row, column=0, sticky="e")
        self.entry_name = tk.Entry(info_frame, width=30)
        self.entry_name.insert(0, self.bunny["name"])
        self.entry_name.grid(row=row, column=1)
        row += 1

        tk.Label(info_frame, text="Gender:").grid(row=row, column=0, sticky="e")
        self.gender_var = tk.StringVar(value=self.bunny["sex"])
        g_frame = tk.Frame(info_frame)
        tk.Radiobutton(g_frame, text="Buck", value="Buck", variable=self.gender_var).pack(side=tk.LEFT)
        tk.Radiobutton(g_frame, text="Doe", value="Doe", variable=self.gender_var).pack(side=tk.LEFT)
        g_frame.grid(row=row, column=1, sticky="w")
        row += 1

        tk.Label(info_frame, text="Color:").grid(row=row, column=0, sticky="e")
        self.entry_color = tk.Entry(info_frame, width=30)
        self.entry_color.insert(0, self.bunny["color"])
        self.entry_color.grid(row=row, column=1)
        row += 1

        tk.Label(info_frame, text="Type:").grid(row=row, column=0, sticky="e")
        self.entry_type = tk.Entry(info_frame, width=30)
        self.entry_type.insert(0, self.bunny["type"])
        self.entry_type.grid(row=row, column=1)
        row += 1

        tk.Label(info_frame, text="Pedigree:").grid(row=row, column=0, sticky="e")
        self.ped_var = tk.StringVar(value="Yes" if self.bunny.get("pedigree") else "No")
        ped_frame = tk.Frame(info_frame)
        tk.Radiobutton(ped_frame, text="Yes", value="Yes", variable=self.ped_var).pack(side=tk.LEFT)
        tk.Radiobutton(ped_frame, text="No", value="No", variable=self.ped_var).pack(side=tk.LEFT)
        ped_frame.grid(row=row, column=1, sticky="w")
        row += 1

        tk.Label(info_frame, text="DOB:").grid(row=row, column=0, sticky="e")
        self.entry_dob = tk.Entry(info_frame, width=30)
        self.entry_dob.insert(0, self.bunny["dob"])
        self.entry_dob.grid(row=row, column=1)
        row += 1

        # IMAGE
        self.label_img = tk.Label(info_frame)
        self.label_img.grid(row=row, column=0, columnspan=2, pady=5)
        row += 1
        self.load_current_image()

        btn_change_img = tk.Button(info_frame, text="Change Image", command=self.change_image)
        btn_change_img.grid(row=row, column=0, columnspan=2, pady=5)
        row += 1

        # MOM / DAD
        tk.Label(info_frame, text="Mom:").grid(row=row, column=0, sticky="e")
        self.mom_var = tk.StringVar()
        mom_name = self.get_parent_name(self.bunny.get("mom_id"))
        self.mom_var.set(mom_name if mom_name else "")
        self.btn_mom = tk.Button(info_frame, textvariable=self.mom_var, command=self.edit_mom)
        self.btn_mom.grid(row=row, column=1, sticky="w")
        row += 1

        tk.Label(info_frame, text="Dad:").grid(row=row, column=0, sticky="e")
        self.dad_var = tk.StringVar()
        dad_name = self.get_parent_name(self.bunny.get("dad_id"))
        self.dad_var.set(dad_name if dad_name else "")
        self.btn_dad = tk.Button(info_frame, textvariable=self.dad_var, command=self.edit_dad)
        self.btn_dad.grid(row=row, column=1, sticky="w")
        row += 1

        tk.Button(self, text="Update Bunny", command=self.update_bunny).pack(pady=5)
        tk.Button(self, text="Delete Bunny", fg="red", command=self.delete_bunny).pack(pady=5)

        bottom_frame = tk.Frame(self)
        bottom_frame.pack()

        # Breeding History
        bh_frame = tk.LabelFrame(bottom_frame, text="Breeding History")
        bh_frame.pack(side=tk.LEFT, padx=10, pady=5)
        self.tree_bh = ttk.Treeview(bh_frame, columns=("DateBred", "Partner", "IsDue?", "RecID"), show="headings")
        self.tree_bh.heading("DateBred", text="Date Bred")
        self.tree_bh.heading("Partner", text="Partner")
        self.tree_bh.heading("IsDue?", text="Is Due?")
        self.tree_bh.heading("RecID", text="RecID")
        self.tree_bh.bind("<Double-1>", self.on_bh_double_click)
        self.tree_bh.pack(fill="both", expand=True)

        # Litter History
        lh_frame = tk.LabelFrame(bottom_frame, text="Litter History")
        lh_frame.pack(side=tk.LEFT, padx=10, pady=5)
        self.tree_lh = ttk.Treeview(lh_frame, columns=("BabyName", "Registered?"), show="headings")
        self.tree_lh.heading("BabyName", text="BabyName")
        self.tree_lh.heading("Registered?", text="Registered?")
        self.tree_lh.bind("<Double-1>", self.on_lh_double_click)
        self.tree_lh.pack(fill="both", expand=True)

        tk.Button(self, text="Close", command=self.destroy).pack(pady=5)

        self.refresh_history_lists()

    def refresh_history_lists(self):
        self.tree_bh.delete(*self.tree_bh.get_children())
        self.tree_lh.delete(*self.tree_lh.get_children())

        data = load_app_data()
        bunny = data["bunnies"].get(self.bunny_id, {})
        bh = bunny.get("breeding_history", [])

        for idx, rec in enumerate(bh):
            date_bred = rec.get("date_bred", "")
            is_due = "Yes" if rec.get("is_due", False) else "No"
            if bunny["sex"] == "Buck":
                partner = rec.get("mom_name", "Unknown")
            else:
                partner = rec.get("dad_name", "Unknown")
            rec_id = f"{self.bunny_id}|{idx}"
            self.tree_bh.insert("", "end", values=(date_bred, partner, is_due, rec_id))

        # fill litter
        for b_id2, b_info2 in data["bunnies"].items():
            if b_id2 == self.bunny_id:
                continue
            if b_info2.get("mom_id") == self.bunny_id or b_info2.get("dad_id") == self.bunny_id:
                reg_str = "❗" if b_info2.get("is_incomplete") else "✔"
                self.tree_lh.insert("", "end", values=(b_info2["name"], reg_str))

    def on_bh_double_click(self, event):
        sel = self.tree_bh.selection()
        if not sel:
            return
        val = self.tree_bh.item(sel[0], "values")
        record_id = val[3]  # self.bunny_id|idx
        parts = record_id.split("|")
        if len(parts) == 2:
            b_id = parts[0]
            idx = int(parts[1])
            BreedingRecordProfile(self, self.controller).set_record(b_id, idx)

    def on_lh_double_click(self, event):
        sel = self.tree_lh.selection()
        if not sel:
            return
        val = self.tree_lh.item(sel[0], "values")
        baby_name = val[0]
        data = load_app_data()
        for bid, info in data["bunnies"].items():
            if info["name"] == baby_name:
                BunnyProfileWindow(self, bid)
                break

    def get_parent_name(self, pid):
        if not pid:
            return ""
        data = load_app_data()
        if pid in data["bunnies"]:
            return data["bunnies"][pid]["name"]
        return ""

    def edit_mom(self):
        data = load_app_data()
        does = []
        for b_id, b_info in data["bunnies"].items():
            if b_info["sex"] == "Doe" and b_id != self.bunny_id:
                does.append(b_info["name"])
        if not does:
            messagebox.showinfo("No Does", "No does found to pick as mom.")
            return
        new_mom = simpledialog.askstring("Select Mom", f"Pick mom from: {does}")
        if new_mom and new_mom in does:
            mom_id = None
            for b_id, b_info in data["bunnies"].items():
                if b_info["name"] == new_mom:
                    mom_id = b_id
                    break
            if mom_id:
                self.bunny["mom_id"] = mom_id
                self.mom_var.set(new_mom)
        else:
            messagebox.showwarning("Invalid", "Invalid mom name, must pick from list.")

    def edit_dad(self):
        data = load_app_data()
        bucks = []
        for b_id, b_info in data["bunnies"].items():
            if b_info["sex"] == "Buck" and b_id != self.bunny_id:
                bucks.append(b_info["name"])
        if not bucks:
            messagebox.showinfo("No Bucks", "No bucks found to pick as dad.")
            return
        new_dad = simpledialog.askstring("Select Dad", f"Pick dad from: {bucks}")
        if new_dad and new_dad in bucks:
            dad_id = None
            for b_id, b_info in data["bunnies"].items():
                if b_info["name"] == new_dad:
                    dad_id = b_id
                    break
            if dad_id:
                self.bunny["dad_id"] = dad_id
                self.dad_var.set(new_dad)
        else:
            messagebox.showwarning("Invalid", "Invalid dad name, must pick from list.")

    def load_current_image(self):
        folder_path = os.path.join(BUNNIES_FOLDER, self.bunny_id)
        image_path = os.path.join(folder_path, self.bunny.get("image_filename", ""))
        if os.path.exists(image_path) and self.bunny["image_filename"]:
            try:
                im = Image.open(image_path)
                im.thumbnail((200, 200))
                self.tk_img = ImageTk.PhotoImage(im)
                self.label_img.configure(image=self.tk_img)
            except Exception as e:
                print("Error loading image:", e)
                self.label_img.configure(text="Image could not be loaded.")
        else:
            self.label_img.configure(text="No image available.")

    def change_image(self):
        new_path = filedialog.askopenfilename(
            title="Select New Bunny Image",
            filetypes=[("Image Files", "*.png;*.jpg;*.jpeg"), ("All files", "*.*")]
        )
        if not new_path:
            return
        if not os.path.exists(new_path):
            messagebox.showerror("Image Error", "Selected file does not exist.")
            return
        folder_path = os.path.join(BUNNIES_FOLDER, self.bunny_id)
        new_filename = compress_and_save_image(new_path, folder_path, self.entry_name.get().strip())
        if new_filename:
            old_file = self.bunny.get("image_filename", "")
            if old_file and old_file != new_filename:
                old_full_path = os.path.join(folder_path, old_file)
                if os.path.exists(old_full_path):
                    os.remove(old_full_path)
            self.bunny["image_filename"] = new_filename
            self.load_current_image()
        else:
            messagebox.showerror("Image Error", "Could not process the selected image.")

    def update_bunny(self):
        old_name = self.bunny["name"]
        new_name = self.entry_name.get().strip()
        new_gender = self.gender_var.get().strip()
        new_color = self.entry_color.get().strip()
        new_type = self.entry_type.get().strip()
        ped_str = self.ped_var.get().strip()
        new_pedigree = (ped_str.lower() == "yes")
        new_dob = self.entry_dob.get().strip()

        if not (new_name and new_gender and new_color and new_type and new_dob):
            messagebox.showwarning("Validation", "All fields are required.")
            return

        data = load_app_data()
        if new_name != old_name:
            update_bunny_name_references(old_name, new_name, self.bunny_id, data)

        self.bunny["name"] = new_name
        self.bunny["sex"] = new_gender
        self.bunny["color"] = new_color
        self.bunny["type"] = new_type
        self.bunny["pedigree"] = new_pedigree
        self.bunny["dob"] = new_dob

        data["bunnies"][self.bunny_id] = self.bunny
        save_app_data(data)
        save_bunny_profile(self.bunny_id, self.bunny)

        messagebox.showinfo("Success", "Bunny information updated.")
        self.destroy()

    def delete_bunny(self):
        resp = messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete '{self.bunny['name']}'?")
        if not resp:
            return
        data = load_app_data()

        for b_id, info in data["bunnies"].items():
            if b_id == self.bunny_id:
                continue
            changed = False
            bh = info.get("breeding_history", [])
            for rec in bh:
                if rec.get("mom_id") == self.bunny_id:
                    rec["mom_id"] = None
                    rec["mom_name"] = "Deleted"
                    changed = True
                if rec.get("dad_id") == self.bunny_id:
                    rec["dad_id"] = None
                    rec["dad_name"] = "Deleted"
                    changed = True
            if changed:
                data["bunnies"][b_id]["breeding_history"] = bh

        del data["bunnies"][self.bunny_id]
        save_app_data(data)

        folder_path = os.path.join(BUNNIES_FOLDER, self.bunny_id)
        if os.path.exists(folder_path):
            shutil.rmtree(folder_path)

        messagebox.showinfo("Deleted", f"Bunny '{self.bunny['name']}' has been deleted.")
        self.destroy()


############################################################################
#  AddBunnyPage
############################################################################
class AddBunnyPage(tk.Frame):
    """Add Bunny with required fields, pick date, browse image, etc."""
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        tk.Label(self, text="Add Bunny", font=("Helvetica", 14, "bold")).pack(pady=10)

        form_frame = tk.Frame(self)
        form_frame.pack(pady=10)

        row = 0
        tk.Label(form_frame, text="Name:").grid(row=row, column=0, sticky="e")
        self.entry_name = tk.Entry(form_frame, width=30)
        self.entry_name.grid(row=row, column=1)
        row += 1

        tk.Label(form_frame, text="Gender:").grid(row=row, column=0, sticky="e")
        self.gender_var = tk.StringVar(value="")
        gender_frame = tk.Frame(form_frame)
        r1 = tk.Radiobutton(gender_frame, text="Buck", value="Buck", variable=self.gender_var)
        r2 = tk.Radiobutton(gender_frame, text="Doe", value="Doe", variable=self.gender_var)
        r1.pack(side=tk.LEFT)
        r2.pack(side=tk.LEFT)
        gender_frame.grid(row=row, column=1, sticky="w")
        row += 1

        tk.Label(form_frame, text="Color:").grid(row=row, column=0, sticky="e")
        self.entry_color = tk.Entry(form_frame, width=30)
        self.entry_color.grid(row=row, column=1)
        row += 1

        tk.Label(form_frame, text="Type:").grid(row=row, column=0, sticky="e")
        self.type_var = tk.StringVar(value="")
        self.combo_type = ttk.Combobox(form_frame, textvariable=self.type_var, width=27)
        self.combo_type["values"] = []
        self.combo_type.grid(row=row, column=1, sticky="w")
        row += 1

        tk.Label(form_frame, text="Pedigree?").grid(row=row, column=0, sticky="e")
        self.pedigree_var = tk.StringVar(value="No")
        pedigree_frame = tk.Frame(form_frame)
        tk.Radiobutton(pedigree_frame, text="Yes", value="Yes", variable=self.pedigree_var).pack(side=tk.LEFT)
        tk.Radiobutton(pedigree_frame, text="No", value="No", variable=self.pedigree_var).pack(side=tk.LEFT)
        pedigree_frame.grid(row=row, column=1, sticky="w")
        row += 1

        tk.Label(form_frame, text="DOB (YYYY-MM-DD):").grid(row=row, column=0, sticky="e")
        self.entry_dob = tk.Entry(form_frame, width=15)
        self.entry_dob.grid(row=row, column=1, sticky="w")
        btn_dob = tk.Button(form_frame, text="Pick", command=self.pick_dob)
        btn_dob.grid(row=row, column=2, padx=5)
        row += 1

        tk.Label(form_frame, text="Image File:").grid(row=row, column=0, sticky="e")
        self.entry_image_path = tk.Entry(form_frame, width=30)
        self.entry_image_path.grid(row=row, column=1)
        btn_browse = tk.Button(form_frame, text="Browse", command=self.browse_image)
        btn_browse.grid(row=row, column=2)
        row += 1

        tk.Label(self, text="All fields are required.", font=("Helvetica", 9, "italic")).pack()
        tk.Button(self, text="Save Bunny", command=self.save_bunny).pack(pady=10)
        tk.Button(self, text="Back to Main Menu",
                  command=lambda: controller.show_frame(MainMenu)).pack()

    def on_show(self):
        self.entry_name.delete(0, tk.END)
        self.gender_var.set("")
        self.entry_color.delete(0, tk.END)
        self.type_var.set("")
        self.pedigree_var.set("No")
        self.entry_dob.delete(0, tk.END)
        self.entry_image_path.delete(0, tk.END)

        known_types = load_types()
        self.combo_type["values"] = list(known_types) + ["Add New Type..."]

    def pick_dob(self):
        picker = DatePicker(self)
        self.wait_window(picker)
        if picker.selected_date:
            self.entry_dob.delete(0, tk.END)
            self.entry_dob.insert(0, str(picker.selected_date))

    def browse_image(self):
        file_path = filedialog.askopenfilename(
            title="Select Bunny Image",
            filetypes=[("Image Files", "*.png;*.jpg;*.jpeg"), ("All files", "*.*")]
        )
        if file_path:
            self.entry_image_path.delete(0, tk.END)
            self.entry_image_path.insert(0, file_path)

    def save_bunny(self):
        name = self.entry_name.get().strip()
        gender = self.gender_var.get().strip()
        color = self.entry_color.get().strip()
        btype = self.type_var.get().strip()
        ped_str = self.pedigree_var.get().strip()
        pedigree = (ped_str.lower() == "yes")
        dob = self.entry_dob.get().strip()
        img_path = self.entry_image_path.get().strip()

        if not (name and gender and color and btype and dob and img_path):
            messagebox.showwarning("Validation", "All fields are required.")
            return

        if not os.path.exists(img_path):
            messagebox.showerror("Image Error", "Selected image file does not exist.")
            return

        data = load_app_data()
        bunny_id = str(uuid.uuid4())
        folder_path = create_bunny_folder(bunny_id)
        saved_image_filename = compress_and_save_image(img_path, folder_path, name)
        if not saved_image_filename:
            messagebox.showerror("Image Error", "Could not process the selected image.")
            return

        if btype == "Add New Type...":
            new_t = simpledialog.askstring("New Type", "Enter new type:")
            if new_t:
                new_t = new_t.strip()
                if new_t:
                    known = load_types()
                    known.append(new_t)
                    save_types(known)
                    btype = new_t
                else:
                    btype = ""
        else:
            known = load_types()
            if btype and btype not in known:
                known.append(btype)
                save_types(known)

        bunny_record = {
            "id": bunny_id,
            "name": name,
            "sex": gender,
            "color": color,
            "type": btype,
            "pedigree": pedigree,
            "dob": dob,
            "image_filename": saved_image_filename,
            "breeding_history": [],
            "mom_id": None,
            "dad_id": None,
            "is_incomplete": False
        }

        data["bunnies"][bunny_id] = bunny_record
        save_app_data(data)
        save_bunny_profile(bunny_id, bunny_record)

        messagebox.showinfo("Success", f"Bunny '{name}' added successfully!")
        self.controller.show_frame(MainMenu)

############################################################################
#  RegisterBabiesPage
############################################################################
class RegisterBabiesPage(tk.Frame):
    """
    Lists all baby bunnies with `is_incomplete=True`.
    Double-click to open a finalization window (similar to older code).
    """
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        tk.Label(self, text="Register Babies", font=("Helvetica", 14, "bold")).pack(pady=5)

        columns = ("Name", "DOB", "MomID", "DadID", "ID")
        self.tree = ttk.Treeview(self, columns=columns, show="headings")
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=100)
        self.tree.bind("<Double-1>", self.on_double_click)
        self.tree.pack(fill="both", expand=True, padx=10, pady=10)

        tk.Button(self, text="Back to Main Menu",
                  command=lambda: controller.show_frame(MainMenu)).pack(pady=5)

    def on_show(self):
        self.refresh_list()

    def refresh_list(self):
        self.tree.delete(*self.tree.get_children())
        data = load_app_data()
        for b_id, b_info in data["bunnies"].items():
            if b_info.get("is_incomplete", False):
                self.tree.insert("", "end", values=(
                    b_info["name"],
                    b_info["dob"],
                    b_info["mom_id"] if b_info["mom_id"] else "None",
                    b_info["dad_id"] if b_info["dad_id"] else "None",
                    b_id
                ))

    def on_double_click(self, event):
        sel = self.tree.selection()
        if not sel:
            return
        val = self.tree.item(sel[0], "values")
        bunny_id = val[4]
        BabyRegisterWindow(self, bunny_id)

    def refresh_after_edit(self):
        self.refresh_list()

class BabyRegisterWindow(tk.Toplevel):
    """
    Similar to 'Add Bunny' form, but pre-filled with partial data. 
    Must fill in mandatory fields. 
    Once complete, set `is_incomplete=False`.
    """
    def __init__(self, parent, bunny_id):
        super().__init__(parent)
        self.title("Register Baby")
        self.bunny_id = bunny_id
        self.parent_page = parent

        data = load_app_data()
        self.bunny = data["bunnies"][bunny_id]

        tk.Label(self, text=f"Register baby: {self.bunny['name']}",
                 font=("Helvetica", 12, "bold")).pack(pady=5)

        form_frame = tk.Frame(self)
        form_frame.pack(pady=5)

        row = 0
        tk.Label(form_frame, text="Name:").grid(row=row, column=0, sticky="e")
        self.entry_name = tk.Entry(form_frame, width=30)
        self.entry_name.insert(0, self.bunny["name"])
        self.entry_name.grid(row=row, column=1)
        row += 1

        tk.Label(form_frame, text="Gender (Buck/Doe):").grid(row=row, column=0, sticky="e")
        self.gender_var = tk.StringVar(value=self.bunny.get("sex", ""))
        gf = tk.Frame(form_frame)
        tk.Radiobutton(gf, text="Buck", value="Buck", variable=self.gender_var).pack(side=tk.LEFT)
        tk.Radiobutton(gf, text="Doe", value="Doe", variable=self.gender_var).pack(side=tk.LEFT)
        gf.grid(row=row, column=1, sticky="w")
        row += 1

        tk.Label(form_frame, text="Color:").grid(row=row, column=0, sticky="e")
        self.entry_color = tk.Entry(form_frame, width=30)
        self.entry_color.insert(0, self.bunny.get("color", ""))
        self.entry_color.grid(row=row, column=1)
        row += 1

        tk.Label(form_frame, text="Type:").grid(row=row, column=0, sticky="e")
        self.type_var = tk.StringVar()
        self.combo_type = ttk.Combobox(form_frame, textvariable=self.type_var, width=27)
        self.combo_type["values"] = []
        self.combo_type.grid(row=row, column=1, sticky="w")
        row += 1

        tk.Label(form_frame, text="Pedigree?").grid(row=row, column=0, sticky="e")
        self.ped_var = tk.StringVar(value="Yes" if self.bunny.get("pedigree") else "No")
        pedf = tk.Frame(form_frame)
        tk.Radiobutton(pedf, text="Yes", value="Yes", variable=self.ped_var).pack(side=tk.LEFT)
        tk.Radiobutton(pedf, text="No", value="No", variable=self.ped_var).pack(side=tk.LEFT)
        pedf.grid(row=row, column=1, sticky="w")
        row += 1

        tk.Label(form_frame, text="DOB:").grid(row=row, column=0, sticky="e")
        self.entry_dob = tk.Entry(form_frame, width=15)
        self.entry_dob.insert(0, self.bunny.get("dob", ""))
        self.entry_dob.grid(row=row, column=1, sticky="w")
        btn_dob = tk.Button(form_frame, text="Pick", command=self.pick_dob)
        btn_dob.grid(row=row, column=2, padx=5)
        row += 1

        tk.Label(form_frame, text="Image File:").grid(row=row, column=0, sticky="e")
        self.entry_image_path = tk.Entry(form_frame, width=30)
        self.entry_image_path.grid(row=row, column=1)
        btn_browse = tk.Button(form_frame, text="Browse", command=self.browse_image)
        btn_browse.grid(row=row, column=2)
        row += 1

        tk.Button(self, text="Finalize", command=self.finalize_baby).pack(pady=10)
        tk.Button(self, text="Cancel", command=self.destroy).pack()

        known_types = load_types()
        self.combo_type["values"] = list(known_types) + ["Add New Type..."]
        self.type_var.set(self.bunny.get("type", ""))

    def pick_dob(self):
        picker = DatePicker(self)
        self.wait_window(picker)
        if picker.selected_date:
            self.entry_dob.delete(0, tk.END)
            self.entry_dob.insert(0, str(picker.selected_date))

    def browse_image(self):
        file_path = filedialog.askopenfilename(
            title="Select Bunny Image",
            filetypes=[("Image Files", "*.png;*.jpg;*.jpeg"), ("All files", "*.*")]
        )
        if file_path:
            self.entry_image_path.delete(0, tk.END)
            self.entry_image_path.insert(0, file_path)

    def finalize_baby(self):
        new_name = self.entry_name.get().strip()
        new_gender = self.gender_var.get().strip()
        new_color = self.entry_color.get().strip()
        new_type = self.type_var.get().strip()
        ped_str = self.ped_var.get().strip()
        new_pedigree = (ped_str.lower() == "yes")
        new_dob = self.entry_dob.get().strip()
        img_path = self.entry_image_path.get().strip()

        if not (new_name and new_gender and new_color and new_type and new_dob):
            messagebox.showwarning("Validation", "All fields except image are required.")
            return

        data = load_app_data()
        baby = data["bunnies"][self.bunny_id]

        if img_path:
            if not os.path.exists(img_path):
                messagebox.showerror("Image Error", "Selected image file does not exist.")
                return
            folder_path = create_bunny_folder(self.bunny_id)
            saved_img = compress_and_save_image(img_path, folder_path, new_name)
            if not saved_img:
                messagebox.showerror("Image Error", "Could not process the selected image.")
                return
            baby["image_filename"] = saved_img

        known = load_types()
        if new_type == "Add New Type...":
            new_type_input = simpledialog.askstring("New Type", "Enter new type:")
            if new_type_input:
                new_type_input = new_type_input.strip()
                if new_type_input:
                    known.append(new_type_input)
                    save_types(known)
                    new_type = new_type_input
                else:
                    new_type = ""
        else:
            if new_type and new_type not in known:
                known.append(new_type)
                save_types(known)

        old_name = baby["name"]
        if new_name != old_name:
            update_bunny_name_references(old_name, new_name, self.bunny_id, data)

        baby["name"] = new_name
        baby["sex"] = new_gender
        baby["color"] = new_color
        baby["type"] = new_type
        baby["pedigree"] = new_pedigree
        baby["dob"] = new_dob
        baby["is_incomplete"] = False

        data["bunnies"][self.bunny_id] = baby
        save_app_data(data)
        save_bunny_profile(self.bunny_id, baby)

        messagebox.showinfo("Success", f"Baby '{new_name}' registered!")
        self.parent_page.refresh_after_edit()
        self.destroy()

############################################################################
#  ListBunniesPage
############################################################################
class ListBunniesPage(tk.Frame):
    """List all complete bunnies. Double-click -> open BunnyProfileWindow."""
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        tk.Label(self, text="Bunny List", font=("Helvetica", 14, "bold")).pack(pady=5)

        columns = ("Name", "Gender", "Color", "Type", "DOB", "Pedigree", "ID")
        self.tree = ttk.Treeview(self, columns=columns, show="headings")
        for col in columns:
            self.tree.heading(col, text=col, command=lambda c=col: self.sort_by_column(c, False))
            self.tree.column(col, width=100)
        self.tree.bind("<Double-1>", self.on_double_click)
        self.tree.pack(fill="both", expand=True, padx=10, pady=10)

        tk.Button(self, text="Back to Main Menu",
                  command=lambda: controller.show_frame(MainMenu)).pack(pady=5)

    def on_show(self):
        self.refresh_list()

    def refresh_list(self):
        self.tree.delete(*self.tree.get_children())
        data = load_app_data()
        bunnies = [b for b in data["bunnies"].values() if not b.get("is_incomplete", False)]
        bunnies.sort(key=lambda x: x["name"].lower())
        for b in bunnies:
            self.tree.insert("", "end", values=(
                b["name"],
                b["sex"],
                b["color"],
                b["type"],
                b["dob"],
                "Yes" if b.get("pedigree") else "No",
                b["id"]
            ))

    def on_double_click(self, event):
        sel = self.tree.selection()
        if not sel:
            return
        vals = self.tree.item(sel[0], "values")
        bunny_id = vals[6]
        BunnyProfileWindow(self, bunny_id)

    def sort_by_column(self, col, descending):
        data_list = []
        for child_id in self.tree.get_children():
            data_list.append((child_id, self.tree.item(child_id, "values")))
        col_map = {
            "Name": 0, "Gender": 1, "Color": 2,
            "Type": 3, "DOB": 4, "Pedigree": 5, "ID": 6
        }
        idx = col_map[col]
        if col in ["Name", "Color", "Type"]:
            data_list.sort(key=lambda x: x[1][idx].lower(), reverse=descending)
        else:
            data_list.sort(key=lambda x: x[1][idx], reverse=descending)
        for i, (child_id, vals) in enumerate(data_list):
            self.tree.move(child_id, "", i)
        self.tree.heading(col, command=lambda c=col: self.sort_by_column(c, not descending))

############################################################################
#  BreedingHistoryPage
############################################################################
class BreedingHistoryPage(tk.Frame):
    """
    List all breeding records from all bunnies in chronological order.
    We only show each record once, typically associated with the Doe.
    """
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        tk.Label(self, text="Breeding History", font=("Helvetica", 14, "bold")).pack(pady=5)

        columns = ("DateBred", "Buck", "Doe", "IsDue?", "IDRecord")
        self.tree = ttk.Treeview(self, columns=columns, show="headings")
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=120)
        self.tree.bind("<Double-1>", self.on_double_click)
        self.tree.pack(fill="both", expand=True, padx=10, pady=10)

        tk.Button(self, text="Back to Main Menu",
                  command=lambda: controller.show_frame(MainMenu)).pack(pady=5)

    def on_show(self):
        self.refresh_list()

    def refresh_list(self):
        self.tree.delete(*self.tree.get_children())
        data = load_app_data()

        # We'll gather each record only once (prefer listing under the Doe)
        seen_records = set()
        for b_id, bunny in data["bunnies"].items():
            bh = bunny.get("breeding_history", [])
            for idx, rec in enumerate(bh):
                # create a "key" that identifies the record
                rec_key = (rec.get("date_bred", ""), rec.get("mom_id"), rec.get("dad_id"))
                if rec_key in seen_records:
                    continue
                # if bunny is Buck, check if there's a mom_id we can show it under
                if bunny["sex"] == "Buck":
                    # let's see if we can find the mom's record
                    mom_id = rec.get("mom_id")
                    if mom_id in data["bunnies"]:
                        # we'll skip this one (since we want to show it under the doe)
                        # unless there's no mom
                        if mom_id:
                            seen_records.add(rec_key)
                            continue

                # Otherwise, we show it
                seen_records.add(rec_key)
                date_bred = rec.get("date_bred", "")
                is_due = "Yes" if rec.get("is_due", False) else "No"

                # figure out buck/doe name
                buck_name = rec.get("dad_name", "Unknown")
                doe_name = rec.get("mom_name", "Unknown")
                # We'll store the record ID as b_id|idx, so we can open from parent's perspective
                rec_id = f"{b_id}|{idx}"
                self.tree.insert("", "end", values=(date_bred, buck_name, doe_name, is_due, rec_id))

    def on_double_click(self, event):
        sel = self.tree.selection()
        if not sel:
            return
        val = self.tree.item(sel[0], "values")
        record_id = val[4]
        parts = record_id.split("|")
        if len(parts) == 2:
            b_id = parts[0]
            idx = int(parts[1])
            self.controller.frames[BreedingRecordProfile].set_record(b_id, idx)
            self.controller.show_frame(BreedingRecordProfile)

############################################################################
#  BreedingRecordProfile
############################################################################
class BreedingRecordProfile(tk.Frame):
    """
    A single breeding record's details:
      - Buck on left, Doe on right, toggles, #born/alive, etc.
    """
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.record_bunny_id = None
        self.record_index = None

        tk.Label(self, text="Breeding Record Profile", font=("Helvetica", 14, "bold")).pack(pady=5)

        top_frame = tk.Frame(self)
        top_frame.pack(pady=5, fill="x")

        self.buck_frame = tk.Frame(top_frame)
        self.buck_frame.pack(side=tk.LEFT, padx=10)

        self.center_line = tk.Frame(top_frame, width=2, bg="black")
        self.center_line.pack(side=tk.LEFT, fill="y")

        self.doe_frame = tk.Frame(top_frame)
        self.doe_frame.pack(side=tk.LEFT, padx=10)

        mid_frame = tk.Frame(self)
        mid_frame.pack(pady=5)

        row = 0
        tk.Label(mid_frame, text="Is Due?").grid(row=row, column=0, sticky="e")
        self.is_due_var = tk.StringVar(value="No")
        due_frame = tk.Frame(mid_frame)
        tk.Radiobutton(due_frame, text="Yes", value="Yes", variable=self.is_due_var,
                       command=self.update_due_state).pack(side=tk.LEFT)
        tk.Radiobutton(due_frame, text="No", value="No", variable=self.is_due_var,
                       command=self.update_due_state).pack(side=tk.LEFT)
        due_frame.grid(row=row, column=1, sticky="w")
        row += 1

        tk.Label(mid_frame, text="Missed Litter?").grid(row=row, column=0, sticky="e")
        self.missed_var = tk.BooleanVar(value=False)
        tk.Checkbutton(mid_frame, variable=self.missed_var, command=self.update_due_state).grid(row=row, column=1, sticky="w")
        row += 1

        tk.Label(mid_frame, text="Number Born:").grid(row=row, column=0, sticky="e")
        self.entry_num_born = tk.Entry(mid_frame, width=5)
        self.entry_num_born.grid(row=row, column=1, sticky="w")
        row += 1

        tk.Label(mid_frame, text="Number Alive:").grid(row=row, column=0, sticky="e")
        self.entry_num_alive = tk.Entry(mid_frame, width=5)
        self.entry_num_alive.grid(row=row, column=1, sticky="w")
        row += 1

        tk.Label(mid_frame, text="Actual Birth Date:").grid(row=row, column=0, sticky="e")
        self.entry_actual_birth = tk.Entry(mid_frame, width=15)
        self.entry_actual_birth.grid(row=row, column=1, sticky="w")
        btn_actual_pick = tk.Button(mid_frame, text="Pick Date", command=self.pick_actual_birth_date)
        btn_actual_pick.grid(row=row, column=2, padx=5)
        row += 1

        tk.Button(self, text="Update Record", command=self.update_record).pack(pady=5)

        self.litter_list_frame = tk.LabelFrame(self, text="Litter Record List")
        self.litter_list_frame.pack(padx=10, pady=5, fill="both", expand=True)
        self.tree_litter = ttk.Treeview(
            self.litter_list_frame,
            columns=("BunnyName", "Registered?"),
            show="headings"
        )
        self.tree_litter.heading("BunnyName", text="Bunny Name")
        self.tree_litter.heading("Registered?", text="Registered?")
        self.tree_litter.bind("<Double-1>", self.on_litter_double_click)
        self.tree_litter.pack(fill="both", expand=True)

        tk.Button(self, text="Back to Breeding History",
                  command=lambda: controller.show_frame(BreedingHistoryPage)).pack(pady=5)

    def pick_actual_birth_date(self):
        if self.is_due_var.get() == "Yes":
            return
        picker = DatePicker(self)
        self.wait_window(picker)
        if picker.selected_date:
            self.entry_actual_birth.delete(0, tk.END)
            self.entry_actual_birth.insert(0, str(picker.selected_date))

    def set_record(self, bunny_id, index):
        self.record_bunny_id = bunny_id
        self.record_index = index
        self.refresh_record()

    def refresh_record(self):
        data = load_app_data()
        bunny = data["bunnies"][self.record_bunny_id]
        bh = bunny.get("breeding_history", [])
        if self.record_index >= len(bh):
            messagebox.showerror("Error", "Invalid breeding record index.")
            return
        rec = bh[self.record_index]

        # if bunny is buck, partner is mom, else partner is dad
        if bunny["sex"] == "Buck":
            buck_id = self.record_bunny_id
            doe_id = rec.get("mom_id")
        else:
            doe_id = self.record_bunny_id
            buck_id = rec.get("dad_id")

        # load buck
        buck_info = data["bunnies"].get(buck_id, {})
        buck_name = buck_info.get("name", "Unknown")
        buck_type = buck_info.get("type", "?")
        buck_img = None
        if buck_id:
            folder_path = os.path.join(BUNNIES_FOLDER, buck_id)
            ipath = os.path.join(folder_path, buck_info.get("image_filename", ""))
            if os.path.exists(ipath):
                buck_img = ipath

        # load doe
        doe_info = data["bunnies"].get(doe_id, {})
        doe_name = doe_info.get("name", "Unknown")
        doe_type = doe_info.get("type", "?")
        doe_img = None
        if doe_id:
            folder_path = os.path.join(BUNNIES_FOLDER, doe_id)
            ipath = os.path.join(folder_path, doe_info.get("image_filename", ""))
            if os.path.exists(ipath):
                doe_img = ipath

        # Show images
        for w in self.buck_frame.winfo_children():
            w.destroy()
        tk.Label(self.buck_frame, text=buck_name, font=("Helvetica", 12, "bold")).pack()
        tk.Label(self.buck_frame, text=f"({buck_type})", font=("Helvetica", 9, "italic")).pack()
        if buck_img:
            try:
                im = Image.open(buck_img)
                im.thumbnail((150,150))
                tk_im = ImageTk.PhotoImage(im)
                lb = tk.Label(self.buck_frame, image=tk_im)
                lb.pack()
                lb.image = tk_im
            except:
                pass

        for w in self.doe_frame.winfo_children():
            w.destroy()
        tk.Label(self.doe_frame, text=doe_name, font=("Helvetica", 12, "bold")).pack()
        tk.Label(self.doe_frame, text=f"({doe_type})", font=("Helvetica", 9, "italic")).pack()
        if doe_img:
            try:
                im2 = Image.open(doe_img)
                im2.thumbnail((150,150))
                tk_im2 = ImageTk.PhotoImage(im2)
                lb2 = tk.Label(self.doe_frame, image=tk_im2)
                lb2.pack()
                lb2.image = tk_im2
            except:
                pass

        is_due = rec.get("is_due", False)
        self.is_due_var.set("Yes" if is_due else "No")
        missed = rec.get("missed_litter", False)
        self.missed_var.set(missed)

        nb = rec.get("num_born", 0)
        na = rec.get("num_alive", 0)
        abd = rec.get("actual_birth_date", "")

        self.entry_num_born.delete(0, tk.END)
        self.entry_num_alive.delete(0, tk.END)
        self.entry_actual_birth.delete(0, tk.END)

        if nb: self.entry_num_born.insert(0, str(nb))
        if na: self.entry_num_alive.insert(0, str(na))
        if abd: self.entry_actual_birth.insert(0, abd)

        self.tree_litter.delete(*self.tree_litter.get_children())
        # gather babies from mom_id/doe_id and dad_id/buck_id
        mom_id = rec.get("mom_id")
        dad_id = rec.get("dad_id")
        all_babies = []
        for b2_id, b2_info in data["bunnies"].items():
            if b2_id == bunny_id:
                continue
            if (b2_info.get("mom_id") == mom_id and b2_info.get("dad_id") == dad_id) or \
               (b2_info.get("mom_id") == dad_id and b2_info.get("dad_id") == mom_id):
                all_babies.append(b2_info)
        for p in all_babies:
            reg_str = "❗" if p.get("is_incomplete") else "✔"
            self.tree_litter.insert("", "end", values=(p["name"], reg_str))

        self.update_due_state()

    def update_due_state(self):
        if self.is_due_var.get() == "Yes":
            self.entry_num_born.config(state="disabled")
            self.entry_num_alive.config(state="disabled")
            self.entry_actual_birth.config(state="disabled")
        else:
            self.entry_num_born.config(state="normal")
            self.entry_num_alive.config(state="normal")
            self.entry_actual_birth.config(state="normal")
        if self.missed_var.get():
            self.entry_num_born.config(state="disabled")
            self.entry_num_alive.config(state="disabled")

    def update_record(self):
        data = load_app_data()
        bunny = data["bunnies"][self.record_bunny_id]
        bh = bunny.get("breeding_history", [])
        if self.record_index >= len(bh):
            messagebox.showerror("Error", "Invalid breeding record index.")
            return
        rec = bh[self.record_index]

        rec["is_due"] = (self.is_due_var.get() == "Yes")
        rec["missed_litter"] = self.missed_var.get()

        if rec["is_due"]:
            rec["num_born"] = 0
            rec["num_alive"] = 0
            rec["actual_birth_date"] = ""
        else:
            if rec["missed_litter"]:
                rec["num_born"] = 0
                rec["num_alive"] = 0
                rec["actual_birth_date"] = ""
            else:
                nb_str = self.entry_num_born.get().strip()
                na_str = self.entry_num_alive.get().strip()
                nb = int(nb_str) if nb_str.isdigit() else 0
                na = int(na_str) if na_str.isdigit() else 0
                rec["num_born"] = nb
                rec["num_alive"] = na
                abd_str = self.entry_actual_birth.get().strip()
                rec["actual_birth_date"] = abd_str

                if na > 0:
                    mom_id = rec.get("mom_id")
                    dad_id = rec.get("dad_id")
                    mom_name = rec.get("mom_name", "Mom?")
                    dad_name = rec.get("dad_name", "Dad?")
                    for i in range(na):
                        baby_id = str(uuid.uuid4())
                        folder_path = create_bunny_folder(baby_id)
                        baby_name = f"{mom_name[:3]}{dad_name[:3]}_Baby{i+1}"
                        baby_record = {
                            "id": baby_id,
                            "name": baby_name,
                            "sex": "",
                            "color": "",
                            "type": "",
                            "pedigree": False,
                            "dob": abd_str,
                            "image_filename": "",
                            "breeding_history": [],
                            "mom_id": mom_id,
                            "dad_id": dad_id,
                            "is_incomplete": True
                        }
                        data["bunnies"][baby_id] = baby_record
                        save_bunny_profile(baby_id, baby_record)

        bh[self.record_index] = rec
        bunny["breeding_history"] = bh
        data["bunnies"][self.record_bunny_id] = bunny
        save_app_data(data)
        save_bunny_profile(self.record_bunny_id, bunny)

        # also update partner's record
        if bunny["sex"] == "Buck":
            partner_id = rec.get("mom_id")
        else:
            partner_id = rec.get("dad_id")

        if partner_id in data["bunnies"]:
            partner_bh = data["bunnies"][partner_id].get("breeding_history", [])
            for idx2, r2 in enumerate(partner_bh):
                if (r2.get("date_bred") == rec.get("date_bred") and
                    r2.get("mom_id") == rec.get("mom_id") and
                    r2.get("dad_id") == rec.get("dad_id")):
                    partner_bh[idx2] = rec
                    data["bunnies"][partner_id]["breeding_history"] = partner_bh
                    save_app_data(data)
                    save_bunny_profile(partner_id, data["bunnies"][partner_id])
                    break

        messagebox.showinfo("Updated", "Breeding record updated.")
        self.refresh_record()

    def on_litter_double_click(self, event):
        sel = self.tree_litter.selection()
        if not sel:
            return
        val = self.tree_litter.item(sel[0], "values")
        baby_name = val[0]
        data = load_app_data()
        baby_id = None
        for bid, binfo in data["bunnies"].items():
            if binfo["name"] == baby_name:
                baby_id = bid
                break
        if baby_id:
            BunnyProfileWindow(self, baby_id)


############################################################################
#  WhoIsDuePage (only shows DOES)
############################################################################
class WhoIsDuePage(tk.Frame):
    """
    Lists breeding records where is_due=True, but only for does.
    Double-click -> open record. 
    Also includes 'Expected Due Date' = date_bred + 31.
    """
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        tk.Label(self, text="Who Is Due? (Does Only)", font=("Helvetica", 14, "bold")).pack(pady=5)

        columns = ("DateBred", "Buck", "Doe", "ExpectedDue", "RecordID")
        self.tree = ttk.Treeview(self, columns=columns, show="headings")
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=120)
        self.tree.bind("<Double-1>", self.on_double_click)
        self.tree.pack(fill="both", expand=True, padx=10, pady=10)

        tk.Button(self, text="Back to Main Menu",
                  command=lambda: controller.show_frame(MainMenu)).pack(pady=5)

    def on_show(self):
        self.refresh_list()

    def refresh_list(self):
        self.tree.delete(*self.tree.get_children())
        data = load_app_data()
        for b_id, bunny in data["bunnies"].items():
            if bunny["sex"] != "Doe":
                continue  # only show does
            bh = bunny.get("breeding_history", [])
            for idx, rec in enumerate(bh):
                if rec.get("is_due", False):
                    date_bred_str = rec.get("date_bred", "")
                    is_due = rec.get("is_due", False)
                    if not date_bred_str:
                        continue
                    try:
                        date_bred_dt = datetime.datetime.strptime(date_bred_str, "%Y-%m-%d").date()
                        expected_dt = date_bred_dt + datetime.timedelta(days=31)
                        expected_str = str(expected_dt)
                    except:
                        expected_str = "Unknown"

                    buck_name = rec.get("dad_name", "Unknown")
                    doe_name = bunny["name"]

                    rec_id = f"{b_id}|{idx}"
                    self.tree.insert("", "end", values=(date_bred_str, buck_name, doe_name, expected_str, rec_id))

    def on_double_click(self, event):
        sel = self.tree.selection()
        if not sel:
            return
        val = self.tree.item(sel[0], "values")
        record_id = val[4]
        parts = record_id.split("|")
        if len(parts) == 2:
            b_id = parts[0]
            idx = int(parts[1])
            self.controller.frames[BreedingRecordProfile].set_record(b_id, idx)
            self.controller.show_frame(BreedingRecordProfile)


############################################################################
#  UnbredPage
############################################################################
class UnbredPage(tk.Frame):
    """List bunnies with no breeding or no future litters."""
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        tk.Label(self, text="Unbred Bunnies", font=("Helvetica", 14, "bold")).pack(pady=5)
        columns = ("Name", "Gender", "Type", "ID")
        self.tree = ttk.Treeview(self, columns=columns, show="headings")
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=120)
        self.tree.bind("<Double-1>", self.on_double_click)
        self.tree.pack(fill="both", expand=True, padx=10, pady=10)

        tk.Button(self, text="Back to Main Menu",
                  command=lambda: controller.show_frame(MainMenu)).pack(pady=5)

    def on_show(self):
        self.refresh_list()

    def refresh_list(self):
        self.tree.delete(*self.tree.get_children())
        data = load_app_data()
        for b_id, bunny in data["bunnies"].items():
            if bunny.get("is_incomplete", False):
                continue
            bh = bunny.get("breeding_history", [])
            if len(bh) == 0:
                self.tree.insert("", "end", values=(bunny["name"], bunny["sex"], bunny["type"], b_id))

    def on_double_click(self, event):
        sel = self.tree.selection()
        if not sel:
            return
        val = self.tree.item(sel[0], "values")
        b_id = val[3]
        BunnyProfileWindow(self, b_id)


############################################################################
#  LineageMenuPage
############################################################################
class LineageMenuPage(tk.Frame):
    """
    Shows a panning/zooming canvas with bunny cards. 
    Also has a list of unbred + who is due, plus combobox for PDF export.
    """
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        self.img_scale = 1.0

        self.canvas = tk.Canvas(self, bg="white")
        self.canvas.pack(side=tk.LEFT, fill="both", expand=True)

        self.canvas.bind("<ButtonPress-1>", self.on_pan_start)
        self.canvas.bind("<B1-Motion>", self.on_pan_move)
        self.canvas.bind("<MouseWheel>", self.on_zoom)
        self.canvas.bind("<Button-4>", self.on_zoom)
        self.canvas.bind("<Button-5>", self.on_zoom)

        sidebar_frame = tk.Frame(self, bg="#EEE", width=200)
        sidebar_frame.pack(side=tk.LEFT, fill="y")

        tk.Button(sidebar_frame, text="Back to Main Menu",
                  command=lambda: controller.show_frame(MainMenu)).pack(pady=5)

        tk.Label(sidebar_frame, text="Unbred Bunnies", font=("Helvetica", 10, "bold")).pack(pady=5)
        self.list_unbred = tk.Listbox(sidebar_frame, height=10)
        self.list_unbred.pack(fill="both", expand=True, padx=5, pady=5)
        self.list_unbred.bind("<Double-1>", self.on_unbred_double)

        tk.Label(sidebar_frame, text="Who Is Due", font=("Helvetica", 10, "bold")).pack(pady=5)
        self.list_due = tk.Listbox(sidebar_frame, height=10)
        self.list_due.pack(fill="both", expand=True, padx=5, pady=5)
        self.list_due.bind("<Double-1>", self.on_due_double)

        bottom_frame = tk.Frame(sidebar_frame, bg="#EEE")
        bottom_frame.pack(side=tk.BOTTOM, fill="x", pady=5)
        self.combo_pick = ttk.Combobox(bottom_frame, width=25)
        self.combo_pick.pack(side=tk.LEFT, padx=5)
        tk.Button(bottom_frame, text="Download Lineage PDF", command=self.download_lineage_pdf).pack(side=tk.LEFT, padx=5)

    def on_unbred_double(self, event):
        sel = self.list_unbred.curselection()
        if not sel:
            return
        bunny_name = self.list_unbred.get(sel[0])
        data = load_app_data()
        b_id = None
        for bid, info in data["bunnies"].items():
            if info["name"] == bunny_name:
                b_id = bid
                break
        if b_id:
            BunnyProfileWindow(self, b_id)

    def on_due_double(self, event):
        sel = self.list_due.curselection()
        if not sel:
            return
        record_str = self.list_due.get(sel[0])
        # parse if you store references

    def on_show(self):
        self.canvas.delete("all")
        data = load_app_data()

        # fill unbred
        self.list_unbred.delete(0, tk.END)
        for bid, binfo in data["bunnies"].items():
            if binfo.get("is_incomplete"):
                continue
            if len(binfo.get("breeding_history", [])) == 0:
                self.list_unbred.insert(tk.END, binfo["name"])

        # fill who is due
        self.list_due.delete(0, tk.END)
        for bid, binfo in data["bunnies"].items():
            if binfo["sex"] != "Doe":
                continue
            for rec in binfo.get("breeding_history", []):
                if rec.get("is_due", False):
                    self.list_due.insert(tk.END, f"{binfo['name']} - {rec.get('date_bred','')}")

        # populate combo
        all_names = []
        for b_id, b_info in data["bunnies"].items():
            if not b_info.get("is_incomplete", False):
                all_names.append(b_info["name"])
        all_names.sort()
        self.combo_pick["values"] = all_names

        x_start, y_start = 100, 100
        i = 0
        for b_id, bunny in data["bunnies"].items():
            if bunny.get("is_incomplete"):
                continue
            x_card = x_start + (i % 5) * 200
            y_card = y_start + (i // 5) * 150
            self.draw_bunny_card(b_id, bunny, x_card, y_card)
            i += 1

    def draw_bunny_card(self, bunny_id, bunny, x, y):
        card_w = 180
        card_h = 70
        rect_id = self.canvas.create_rectangle(x, y, x+card_w, y+card_h, fill="white", outline="black")

        if bunny["sex"] == "Buck":
            strip_color = "#ADD8E6"
        else:
            strip_color = "#FFC0CB"
        self.canvas.create_rectangle(x+card_w-10, y, x+card_w, y+card_h, fill=strip_color, outline="black")

        folder_path = os.path.join(BUNNIES_FOLDER, bunny_id)
        img_path = os.path.join(folder_path, bunny.get("image_filename", ""))
        if os.path.exists(img_path):
            try:
                im = Image.open(img_path)
                w, h = im.size
                new_w = int(w * self.img_scale)
                new_h = int(h * self.img_scale)
                im = im.resize((new_w, new_h), Image.ANTIALIAS)
                tk_img = ImageTk.PhotoImage(im)
                setattr(self, f"_img_{bunny_id}", tk_img)
                self.canvas.create_image(x+5, y+5, anchor="nw", image=tk_img)
            except:
                pass

        self.canvas.create_text(x+60, y+15, anchor="nw", text=bunny["name"], font=("Helvetica", 10, "bold"))
        self.canvas.create_text(x+60, y+32, anchor="nw", text=bunny["type"], font=("Helvetica", 8, "italic"))

        def open_profile(e, bid=bunny_id):
            BunnyProfileWindow(self, bid)
        self.canvas.tag_bind(rect_id, "<Button-1>", open_profile)

    def on_pan_start(self, event):
        self.scan_mark_x = event.x
        self.scan_mark_y = event.y

    def on_pan_move(self, event):
        self.canvas.scan_dragto(event.x, event.y, gain=1)

    def on_zoom(self, event):
        factor = 1.0
        if event.delta > 0 or event.num == 4:
            factor = 1.1
        elif event.delta < 0 or event.num == 5:
            factor = 0.9
        self.img_scale *= factor
        self.canvas.scale("all", event.x, event.y, factor, factor)
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def download_lineage_pdf(self):
        pick = self.combo_pick.get().strip()
        if not pick:
            messagebox.showwarning("No Bunny", "Select a bunny for lineage PDF.")
            return
        data = load_app_data()
        found_id = None
        for b_id, b_info in data["bunnies"].items():
            if b_info["name"] == pick:
                found_id = b_id
                break
        if not found_id:
            messagebox.showerror("Not Found", f"No bunny named {pick}")
            return

        pdf_path = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf")]
        )
        if not pdf_path:
            return

        try:
            from reportlab.lib.pagesizes import landscape, A4
            from reportlab.pdfgen import canvas
            from reportlab.lib.utils import ImageReader
        except ImportError:
            messagebox.showerror("ReportLab Missing", "Please install reportlab to export PDF.")
            return

        c = canvas.Canvas(pdf_path, pagesize=landscape(A4))
        width, height = landscape(A4)

        ancestry = self.build_ancestry(found_id)
        if not ancestry:
            messagebox.showwarning("No Ancestry", "No ancestry found.")
            return

        x_offset = 50
        y_offset = height - 100

        def draw_bunny_box(bid, x, y):
            data_ = load_app_data()
            binfo_ = data_["bunnies"][bid]
            box_w = 200
            box_h = 60
            c.rect(x, y, box_w, box_h, stroke=1, fill=0)

            if binfo_["sex"] == "Buck":
                c.setFillColorRGB(0.68, 0.85, 0.9)
            else:
                c.setFillColorRGB(1.0, 0.75, 0.8)
            c.rect(x+box_w-10, y, 10, box_h, stroke=1, fill=1)

            c.setFillColorRGB(0,0,0)
            c.setFont("Helvetica-Bold", 10)
            c.drawString(x+60, y+box_h-15, binfo_["name"])
            c.setFont("Helvetica", 8)
            c.drawString(x+60, y+box_h-30, binfo_["type"])

            folder_path = os.path.join(BUNNIES_FOLDER, bid)
            ipath = os.path.join(folder_path, binfo_.get("image_filename", ""))
            if os.path.exists(ipath):
                try:
                    c.drawImage(ImageReader(ipath), x+5, y+5,
                                width=40, height=40, preserveAspectRatio=True)
                except:
                    pass

        main_bunny = ancestry[0][0]
        draw_bunny_box(main_bunny, x_offset, y_offset)
        c.line(x_offset, y_offset-5, x_offset+200, y_offset-5)
        y_offset -= 70

        for g in range(1, len(ancestry)):
            gen_list = ancestry[g]
            x_gen = 50
            for p_id in gen_list:
                draw_bunny_box(p_id, x_gen, y_offset)
                x_gen += 220
            y_offset -= 80

        c.showPage()
        c.save()
        messagebox.showinfo("Exported", f"Lineage PDF saved to {pdf_path}")

    def build_ancestry(self, bunny_id):
        data = load_app_data()
        if bunny_id not in data["bunnies"]:
            return []
        out = [[bunny_id]]
        curr_gen = [bunny_id]
        visited = set([bunny_id])

        for _ in range(4):
            next_gen = []
            for b in curr_gen:
                binfo = data["bunnies"][b]
                mom_id = binfo.get("mom_id")
                dad_id = binfo.get("dad_id")
                if mom_id and mom_id in data["bunnies"] and mom_id not in visited:
                    next_gen.append(mom_id)
                    visited.add(mom_id)
                if dad_id and dad_id in data["bunnies"] and dad_id not in visited:
                    next_gen.append(dad_id)
                    visited.add(dad_id)
            if not next_gen:
                break
            out.append(next_gen)
            curr_gen = next_gen

        return out

############################################################################
#  RecordBreedingPage
############################################################################
class RecordBreedingPage(tk.Frame):
    """
    A page that lets you create a new breeding record with:
      - buck/doe selection
      - breeding date
      - is_due / missed_litter toggles
      - number born / alive (optional at creation time)
    Only one record is created, but appended to both parents.
    """
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        tk.Label(self, text="Record Breeding", font=("Helvetica", 14, "bold")).pack(pady=10)

        form_frame = tk.Frame(self)
        form_frame.pack(pady=10)

        row = 0
        tk.Label(form_frame, text="Select Buck:").grid(row=row, column=0, sticky="e")
        self.buck_var = tk.StringVar()
        self.combo_buck = ttk.Combobox(form_frame, textvariable=self.buck_var, width=30)
        self.combo_buck.grid(row=row, column=1, padx=5, pady=5)
        row += 1

        tk.Label(form_frame, text="Select Doe:").grid(row=row, column=0, sticky="e")
        self.doe_var = tk.StringVar()
        self.combo_doe = ttk.Combobox(form_frame, textvariable=self.doe_var, width=30)
        self.combo_doe.grid(row=row, column=1, padx=5, pady=5)
        row += 1

        tk.Label(form_frame, text="Breeding Date:").grid(row=row, column=0, sticky="e")
        self.entry_breed_date = tk.Entry(form_frame, width=15)
        self.entry_breed_date.grid(row=row, column=1, sticky="w")
        btn_pick_date = tk.Button(form_frame, text="Pick Date", command=self.pick_breed_date)
        btn_pick_date.grid(row=row, column=2, padx=5)
        row += 1

        tk.Label(form_frame, text="Is Due?").grid(row=row, column=0, sticky="e")
        self.is_due_var = tk.StringVar(value="No")
        due_frame = tk.Frame(form_frame)
        tk.Radiobutton(due_frame, text="Yes", value="Yes", variable=self.is_due_var).pack(side=tk.LEFT)
        tk.Radiobutton(due_frame, text="No", value="No", variable=self.is_due_var).pack(side=tk.LEFT)
        due_frame.grid(row=row, column=1, sticky="w")
        row += 1

        tk.Label(form_frame, text="Missed Litter?").grid(row=row, column=0, sticky="e")
        self.missed_var = tk.BooleanVar(value=False)
        tk.Checkbutton(form_frame, variable=self.missed_var).grid(row=row, column=1, sticky="w")
        row += 1

        tk.Label(form_frame, text="Number Born:").grid(row=row, column=0, sticky="e")
        self.entry_num_born = tk.Entry(form_frame, width=5)
        self.entry_num_born.grid(row=row, column=1, sticky="w")
        row += 1

        tk.Label(form_frame, text="Number Alive:").grid(row=row, column=0, sticky="e")
        self.entry_num_alive = tk.Entry(form_frame, width=5)
        self.entry_num_alive.grid(row=row, column=1, sticky="w")
        row += 1

        tk.Button(self, text="Save Breeding", command=self.save_breeding).pack(pady=10)
        tk.Button(self, text="Back to Main Menu",
                  command=lambda: controller.show_frame(MainMenu)).pack()

    def on_show(self):
        self.populate_bunny_dropdowns()
        self.buck_var.set("")
        self.doe_var.set("")
        self.entry_breed_date.delete(0, tk.END)
        self.is_due_var.set("No")
        self.missed_var.set(False)
        self.entry_num_born.delete(0, tk.END)
        self.entry_num_alive.delete(0, tk.END)

    def populate_bunny_dropdowns(self):
        data = load_app_data()
        buck_options = []
        doe_options = []
        for b_id, b_info in data["bunnies"].items():
            if b_info.get("is_incomplete"):
                continue
            if b_info["sex"] == "Buck":
                buck_options.append(b_info["name"])
            elif b_info["sex"] == "Doe":
                doe_options.append(b_info["name"])
        buck_options.sort()
        doe_options.sort()
        self.combo_buck["values"] = buck_options
        self.combo_doe["values"] = doe_options

    def pick_breed_date(self):
        picker = DatePicker(self)
        self.wait_window(picker)
        if picker.selected_date:
            self.entry_breed_date.delete(0, tk.END)
            self.entry_breed_date.insert(0, str(picker.selected_date))

    def save_breeding(self):
        buck_name = self.buck_var.get().strip()
        doe_name = self.doe_var.get().strip()
        if not buck_name or not doe_name:
            messagebox.showwarning("Validation", "Buck and Doe are required.")
            return
        breed_date_str = self.entry_breed_date.get().strip()
        if not breed_date_str:
            messagebox.showwarning("Validation", "Breeding date is required.")
            return

        is_due = (self.is_due_var.get() == "Yes")
        missed = self.missed_var.get()

        nb_str = self.entry_num_born.get().strip()
        na_str = self.entry_num_alive.get().strip()
        nb = int(nb_str) if nb_str.isdigit() else 0
        na = int(na_str) if na_str.isdigit() else 0

        data = load_app_data()
        buck_id = None
        doe_id = None

        for b_id, info in data["bunnies"].items():
            if info["name"] == buck_name:
                buck_id = b_id
            if info["name"] == doe_name:
                doe_id = b_id

        if not buck_id or not doe_id:
            messagebox.showerror("Error", "Could not find buck/doe by that name.")
            return

        record_for_both = {
            "date_bred": breed_date_str,
            "mom_name": doe_name,
            "mom_id": doe_id,
            "dad_name": buck_name,
            "dad_id": buck_id,
            "is_due": is_due,
            "missed_litter": missed,
            "num_born": nb,
            "num_alive": na,
            "actual_birth_date": ""
        }

        # store in both bunnies
        data["bunnies"][buck_id].setdefault("breeding_history", [])
        data["bunnies"][buck_id]["breeding_history"].append(record_for_both)

        data["bunnies"][doe_id].setdefault("breeding_history", [])
        data["bunnies"][doe_id]["breeding_history"].append(record_for_both)

        # if num_alive>0 and not missed_litter
        if not is_due and not missed and na>0:
            # create placeholders
            for i in range(na):
                baby_id = str(uuid.uuid4())
                folder = create_bunny_folder(baby_id)
                baby_name = f"{doe_name[:3]}{buck_name[:3]}_Baby{i+1}"
                baby_rec = {
                    "id": baby_id,
                    "name": baby_name,
                    "sex": "",
                    "color": "",
                    "type": "",
                    "pedigree": False,
                    "dob": breed_date_str,  # or blank
                    "image_filename": "",
                    "breeding_history": [],
                    "mom_id": doe_id,
                    "dad_id": buck_id,
                    "is_incomplete": True
                }
                data["bunnies"][baby_id] = baby_rec
                save_bunny_profile(baby_id, baby_rec)

        save_app_data(data)
        messagebox.showinfo("Success", "Breeding recorded successfully.")
        self.controller.show_frame(MainMenu)

############################################################################
#  MAIN MENU
############################################################################
class MainMenu(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        tk.Label(self, text="Bunny Breeding - Main Menu",
                 font=("Helvetica", 16, "bold")).pack(pady=10)

        tk.Button(self, text="Add New Bunny",
                  command=lambda: controller.show_frame(AddBunnyPage)).pack(pady=5)

        tk.Button(self, text="Register Babies",
                  command=lambda: controller.show_frame(RegisterBabiesPage)).pack(pady=5)

        tk.Button(self, text="Record Breeding",
                  command=lambda: controller.show_frame(RecordBreedingPage)).pack(pady=5)

        tk.Button(self, text="Bunny List",
                  command=lambda: controller.show_frame(ListBunniesPage)).pack(pady=5)

        tk.Button(self, text="Breeding History",
                  command=lambda: controller.show_frame(BreedingHistoryPage)).pack(pady=5)

        tk.Button(self, text="Who Is Due?",
                  command=lambda: controller.show_frame(WhoIsDuePage)).pack(pady=5)

        tk.Button(self, text="Unbred Bunnies",
                  command=lambda: controller.show_frame(UnbredPage)).pack(pady=5)

        tk.Button(self, text="Lineage Menu",
                  command=lambda: controller.show_frame(LineageMenuPage)).pack(pady=5)

        tk.Button(self, text="Exit", command=self.quit).pack(pady=5)

############################################################################
#  BUNNYBREEDERAPP
############################################################################
class BunnyBreederApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Bunny Breeding - Ultimate Edition")
        ensure_directories()

        container = tk.Frame(self)
        container.pack(side="top", fill="both", expand=True)

        self.frames = {}
        for F in (
            MainMenu,
            AddBunnyPage,
            RegisterBabiesPage,
            RecordBreedingPage,
            ListBunniesPage,
            BreedingHistoryPage,
            BreedingRecordProfile,
            WhoIsDuePage,
            UnbredPage,
            LineageMenuPage
        ):
            frame = F(parent=container, controller=self)
            self.frames[F] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        self.show_frame(MainMenu)

    def show_frame(self, cont):
        frame = self.frames[cont]
        if hasattr(frame, "on_show"):
            frame.on_show()
        frame.tkraise()

############################################################################
#  MAIN LAUNCH
############################################################################
if __name__ == "__main__":
    ensure_directories()
    app_data = load_app_data()
    app = BunnyBreederApp()
    app.mainloop()
