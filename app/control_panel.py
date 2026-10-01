"""A bilingual, keyboard-accessible studio for the desktop companions."""
from pathlib import Path
import sys
import tkinter as tk
from tkinter import ttk, font
from app.dragon_personality import PERCH_POWERS, MENU_LABELS,AIR_GESTURES

PETS=(('bunny','BooBoo','กระต่ายหูตก','booboo'),
      ('mookrata','Moo Krata','ลูกสุนัข','moo-krata'),
      ('bibi','Bibi','ลูกนกอินทรี','bibi'),
      ('kitten','Tabby Kitten','ลูกแมวขนฟู','kitten'),
      ('dragon','Sleepy Dragon','มังกรดำขี้เซา','dragon'))
GROUPS=(
    ('Personality · บุคลิก',('proud','curious_sniff','happy','belly_smoke','threat','roar','fury')),
    ('Move & Fly · เคลื่อนไหว',('ground_walk','run','run_glide','walk','hover_float','dive_recover','air_brake','roll','perch_landing')),
    ('Elemental Magic · พลังธาตุ',('ember_bubbles','static_charge','aurora_breath','thunder_roar','fire','smoke','cloud_flame','storm_hover','wing_gust')),
)
LABELS={state:label for label,state in MENU_LABELS}
LABELS.update({'ground_walk':'Walk (เดิน)','run':'Run (วิ่ง)','run_glide':'Run & Low Glide (วิ่งแล้วร่อนใกล้พื้น)','walk':'Soaring Flight (บินร่อน)',
              'belly_smoke':'Belly-up Smoke (นอนหงายพ่นควัน)','threat':'Warning (ขู่กางปีก)',
              'roar':'Roar (คำราม)','fury':'Fury (โกรธจัด)','fire':'Flame Breath (พ่นไฟ)',
              'smoke':'Smoke Ring (วงควัน)','cloud_flame':'Jade Cloud Ignition (เมฆแก๊สติดไฟ)',
              'storm_hover':'Horn Lightning (สายฟ้าจากเขา)','wing_gust':'Wing Whirlwind (พายุจากปีก)'})


class ControlPanel:
    def __init__(self,pet):
        self.pet=pet;self.closed=False;self.images=[];self.cards={};self.actions={}
        self.window=tk.Toplevel(pet.root)
        self.window.title('Pet Studio — Cute Desktop Pet')
        self.window.configure(bg='#f5f7fc')
        left,top,right,bottom=pet.work_area
        width=min(920,max(600,right-left-40));height=min(760,max(480,bottom-top-40))
        self.window.geometry(f'{width}x{height}{left+20:+d}{top+20:+d}')
        self.window.minsize(580,440)
        self.window.protocol('WM_DELETE_WINDOW',self.hide)
        self.window.bind('<Escape>',lambda event:self.hide())
        self.window.bind('<Control-space>',lambda event:self.toggle_pause())
        self.family=font.nametofont('TkDefaultFont').actual('family')
        self._styles()
        self.status=tk.StringVar();self.message=tk.StringVar(value='Choose a pet, then try a gesture. / เลือกสัตว์ แล้วลองพฤติกรรมได้เลย')
        outer=ttk.Frame(self.window,style='Studio.TFrame',padding=22);outer.pack(fill='both',expand=True)
        header=ttk.Frame(outer,style='Studio.TFrame');header.pack(fill='x')
        titles=ttk.Frame(header,style='Studio.TFrame');titles.pack(side='left',fill='x',expand=True)
        ttk.Label(titles,text='Your little desktop world',style='Hero.Studio.TLabel').pack(anchor='w')
        ttk.Label(titles,text='Pet Studio · เพื่อนตัวน้อยบนหน้าจอ',style='Muted.Studio.TLabel').pack(anchor='w',pady=(4,10))
        self.pause=ttk.Button(header,command=self.toggle_pause,style='Primary.Studio.TButton');self.pause.pack(side='right')
        ttk.Label(outer,textvariable=self.status,style='Status.Studio.TLabel',padding=(12,9)).pack(fill='x',pady=(0,14))
        notebook=ttk.Notebook(outer,style='Studio.TNotebook');self.notebook=notebook;notebook.pack(fill='both',expand=True)
        pets=ttk.Frame(notebook,style='Studio.TFrame',padding=16)
        dragon=ttk.Frame(notebook,style='Studio.TFrame',padding=16)
        settings=ttk.Frame(notebook,style='Studio.TFrame',padding=20)
        notebook.add(pets,text='  Companions · สัตว์เลี้ยง  ')
        notebook.add(dragon,text='  Dragon · มังกร  ')
        notebook.add(settings,text='  Settings · ตั้งค่า  ')
        self._pets(pets);self._dragon(dragon);self._settings(settings)
        ttk.Label(outer,textvariable=self.message,style='Muted.Studio.TLabel',wraplength=820).pack(fill='x',pady=(12,0))
        ttk.Label(outer,text='Drag to move · ลากเพื่อย้าย   |   Double-click to open Studio · ดับเบิลคลิกเปิดหน้าควบคุม',style='Hint.Studio.TLabel').pack(anchor='w',pady=(5,0))
        self._refresh();self.show()

    def _styles(self):
        s=ttk.Style(self.window)
        # Clam is bundled with Tk on both supported platforms.
        s.theme_use('clam')
        s.configure('Studio.TFrame',background='#f5f7fc')
        s.configure('Studio.TLabel',background='#f5f7fc',foreground='#1c2940',font=(self.family,10))
        s.configure('Hero.Studio.TLabel',font=(self.family,22,'bold'))
        s.configure('Muted.Studio.TLabel',foreground='#627088',font=(self.family,10))
        s.configure('Hint.Studio.TLabel',foreground='#627088',font=(self.family,9))
        s.configure('Status.Studio.TLabel',background='#e9eef9',foreground='#29426b')
        s.configure('Studio.TButton',font=(self.family,10),padding=(12,10),background='#ffffff',foreground='#26334b',borderwidth=1)
        s.map('Studio.TButton',background=[('disabled','#edf0f5'),('pressed','#d8e5fb'),('active','#e8f0ff')],foreground=[('disabled','#8993a2')])
        s.configure('Primary.Studio.TButton',background='#365bd8',foreground='white',padding=(16,11))
        s.map('Primary.Studio.TButton',background=[('active','#284bbd'),('pressed','#213d9e')],foreground=[('active','white')])
        s.configure('Selected.Studio.TButton',background='#dfe9ff',foreground='#2649b4')
        s.configure('Studio.TNotebook',background='#f5f7fc',borderwidth=0)
        s.configure('Studio.TNotebook.Tab',padding=(10,9),font=(self.family,10))
        s.map('Studio.TNotebook.Tab',background=[('selected','#ffffff')],foreground=[('selected','#2649b4')])
        s.configure('Studio.TCheckbutton',background='#f5f7fc',font=(self.family,11),padding=(0,8))
        s.configure('Studio.TRadiobutton',background='#f5f7fc',font=(self.family,10),padding=8)

    def _pets(self,frame):
        ttk.Label(frame,text='Pick your companion · เลือกเพื่อนตัวน้อย',style='Studio.TLabel').grid(row=0,column=0,columnspan=3,sticky='w',pady=(0,12))
        base=Path(getattr(sys,'_MEIPASS',Path(__file__).resolve().parents[1]))
        for i,(key,name,thai,image_name) in enumerate(PETS):
            image=tk.PhotoImage(master=self.window,file=str(base/f'assets/ui/{image_name}.png'))
            scale=max(1,(max(image.width(),image.height())+109)//110)
            image=image.subsample(scale,scale);self.images.append(image)
            button=ttk.Button(frame,text=f'{name}\n{thai}',image=image,compound='top',style='Studio.TButton',command=lambda k=key:self.select(k))
            button.grid(row=1+i//3,column=i%3,sticky='nsew',padx=5,pady=5)
            self.cards[key]=button
        for col in range(3):frame.columnconfigure(col,weight=1)
        frame.rowconfigure(1,weight=1);frame.rowconfigure(2,weight=1)
        ttk.Button(frame,text='More Characters\nตัวละครอื่น ๆ',style='Studio.TButton',command=self.more_characters).grid(row=2,column=2,sticky='nsew',padx=5,pady=5)

    def _dragon(self,frame):
        ttk.Label(frame,text='Try a gesture · เลือกท่าที่อยากเห็น',style='Studio.TLabel').pack(anchor='w')
        ttk.Label(frame,text='Select Sleepy Dragon first. Ground skills play after landing.\nเลือกมังกรก่อน ท่าบนพื้นใช้ได้เมื่อลงจอดแล้ว',style='Muted.Studio.TLabel').pack(anchor='w',pady=(4,10))
        tabs=ttk.Notebook(frame,style='Studio.TNotebook');tabs.pack(fill='both',expand=True)
        for title,states in GROUPS:
            page=ttk.Frame(tabs,style='Studio.TFrame',padding=10);tabs.add(page,text=title)
            canvas=tk.Canvas(page,bg='#f5f7fc',highlightthickness=0,height=240)
            scrollbar=ttk.Scrollbar(page,orient='vertical',command=canvas.yview)
            scrollbar.pack(side='right',fill='y');canvas.pack(side='left',fill='both',expand=True)
            canvas.configure(yscrollcommand=scrollbar.set)
            content=ttk.Frame(canvas,style='Studio.TFrame')
            item=canvas.create_window((0,0),window=content,anchor='nw')
            content.bind('<Configure>',lambda event,c=canvas:c.configure(scrollregion=c.bbox('all')))
            canvas.bind('<Configure>',lambda event,c=canvas,i=item:c.itemconfigure(i,width=event.width))
            def wheel(event,c=canvas):
                c.yview_scroll(-1 if event.delta>0 else 1,'units')
                return 'break'
            canvas.bind('<MouseWheel>',wheel)
            for i,state in enumerate(states):
                label=LABELS[state].replace(' (','\n(')
                button=ttk.Button(content,text=label,style='Studio.TButton',command=lambda name=state:self.gesture(name))
                button.grid(row=i//3,column=i%3,sticky='nsew',padx=5,pady=5)
                button.bind('<MouseWheel>',wheel)
                self.actions[state]=button
            for col in (0,1,2):content.columnconfigure(col,weight=1)

    def _settings(self,frame):
        ttk.Label(frame,text='Make yourself at home · ปรับให้เหมาะกับคุณ',style='Studio.TLabel').pack(anchor='w',pady=(0,18))
        ttk.Checkbutton(frame,text='Always on top · อยู่เหนือหน้าต่างอื่น',variable=self.pet.topmost_var,command=self.pet._set_topmost,style='Studio.TCheckbutton').pack(anchor='w')
        ttk.Checkbutton(frame,text='Pause movement · พักการเคลื่อนไหว',variable=self.pet.paused_var,command=self.pet._set_paused,style='Studio.TCheckbutton').pack(anchor='w')
        ttk.Label(frame,text='Movement speed · ความเร็ว',style='Studio.TLabel').pack(anchor='w',pady=(20,8))
        row=ttk.Frame(frame,style='Studio.TFrame');row.pack(anchor='w')
        for name,value in (('Slow · ช้า','slow'),('Normal · ปกติ','normal'),('Fast · เร็ว','fast')):
            ttk.Radiobutton(row,text=name,value=value,variable=self.pet.speed_var,command=self.pet._set_speed,style='Studio.TRadiobutton').pack(side='left',padx=(0,14))
        ttk.Button(frame,text='Return to desktop edge · กลับขอบล่าง',command=self.pet._move_to_bottom,style='Studio.TButton').pack(anchor='w',pady=24)
        ttk.Label(frame,text='Natural routines run automatically with rests between gestures.\nสัตว์จะเลือกพฤติกรรมเอง พร้อมช่วงพักระหว่างท่าทาง',style='Muted.Studio.TLabel').pack(anchor='w')

    def select(self,key):
        if key!=self.pet.current_character:
            self.pet.character_var.set(key);self.pet._set_character()
        self.message.set('Companion selected. / เลือกสัตว์แล้ว')
        self.refresh()

    def more_characters(self):
        self.pet.menu.tk_popup(self.window.winfo_rootx()+30,self.window.winfo_rooty()+100)
        self.pet.menu.grab_release()

    def gesture(self,name):
        if name=='walk':self.pet._jump_now();ok=True
        else:ok=self.pet._dragon_gesture(name)
        self.message.set(f'{LABELS[name]} — requested / เลือกท่าแล้ว' if ok else 'Resume and let the dragon land first. / กดเล่นต่อและรอให้มังกรลงจอดก่อน')
        self.refresh()

    def toggle_pause(self):
        self.pet.paused_var.set(not self.pet.paused_var.get());self.pet._set_paused();self.refresh()

    def refresh(self):
        key=self.pet.current_character;paused=self.pet.paused_var.get()
        name=next((name for k,name,_,_ in PETS if k==key),key.replace('_',' ').title())
        behavior=getattr(self.pet.behavior,'state','idle').replace('_',' ').title()
        self.status.set(f'{name}   ·   {"Paused / พักอยู่" if paused else "Playing / กำลังเล่น"}   ·   {behavior}')
        self.pause.configure(text='Resume · เล่นต่อ' if paused else 'Pause · พัก')
        for k,button in self.cards.items():button.configure(style='Selected.Studio.TButton' if key==k else 'Studio.TButton')
        for state,button in self.actions.items():
            allowed=key=='dragon' and not paused and not self.pet.dragging
            if state in AIR_GESTURES or state == 'roll':allowed=allowed and self.pet.dragon_flight.state in {'rest','cruise'}
            else:allowed=allowed and (self.pet.dragon_flight.state=='rest' or (self.pet.dragon_flight.state=='perched' and state in PERCH_POWERS and self.pet.behavior.state=='idle'))
            button.configure(state='normal' if allowed else 'disabled')

    def _refresh(self):
        if self.closed:return
        if self.window.state()!='withdrawn':self.refresh()
        self.timer=self.window.after(500,self._refresh)

    def show(self):
        self.window.deiconify();self.window.lift();self.window.focus_set();self.refresh()

    def hide(self):self.window.withdraw()

    def close(self):
        self.closed=True
        self.window.after_cancel(self.timer)
        self.window.destroy()
