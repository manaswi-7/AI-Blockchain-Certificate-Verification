"""Generate 500 genuine + 500 realistically tampered synthetic certificates.

The certificate layout is kept fixed at 2048x1447. Tampering changes only the
selected content/region and never writes labels such as ORIGINAL, TAMPERED,
FAKE, ALTERED, etc. The visual styling of edited text matches the template.

Output:
  dataset/certificates/real/*.png
  dataset/certificates/tampered/*.png
  dataset/certificates/metadata.csv
"""
from pathlib import Path
import csv
import random
from PIL import Image, ImageDraw, ImageFont
import qrcode

ROOT = Path(__file__).resolve().parent
DATASET = ROOT / "dataset" / "certificates"
REAL = DATASET / "real"
TAMPERED = DATASET / "tampered"

W, H = 2048, 1447
SEED = 20250920

FIRST_NAMES = [
    "Aarav","Aadhya","Abhinav","Aditya","Akash","Akanksha","Amrutha","Ananya",
    "Anirudh","Anjali","Arjun","Ashwin","Bhavana","Chaitanya","Charan","Deepak",
    "Diya","Divya","Eesha","Gautam","Harini","Harsha","Ishita","Jahnavi","Karthik",
    "Keerthi","Krishna","Lakshmi","Manoj","Meghana","Mohan","Nandini","Navya",
    "Neha","Nikhil","Nisha","Pavan","Pranav","Pranitha","Priya","Rahul","Rakesh",
    "Ravi","Riya","Rohit","Sahana","Saketh","Sanjana","Sanjay","Shreya","Siddharth",
    "Sneha","Srinivas","Srujana","Swathi","Tanvi","Tejas","Vaishnavi","Varun",
    "Vasavi","Vignesh","Vijay","Vishal","Yash","Yamini"
]
LAST_NAMES = [
    "Reddy","Rao","Sharma","Patel","Kumar","Singh","Nair","Iyer","Varma","Verma",
    "Naidu","Goud","Gupta","Mehta","Joshi","Deshmukh","Das","Mishra","Khan","Bose",
    "Chowdary","Kandula","Pothula","Vemula","Konda","Yadav","Bansal","Agarwal",
    "Kapoor","Malhotra","Menon","Pillai","Shetty","Hegde","Kulkarni","Jain"
]
DEPARTMENTS = ["Information Technology","Computer Science","Artificial Intelligence",
               "Electronics and Communication","Electrical Engineering"]
COURSES = [
    ("CS401","Machine Learning",4),("CS402","Database Systems",3),
    ("CS403","Artificial Intelligence",4),("CS404","Computer Networks",3),
    ("CS405","Data Mining",4),("CS406","Software Engineering",3)
]
GRADES = [("O",10),("A+",9),("A",8),("B+",7),("B",6)]
TAMPERS = ["name","date","certificate_id","roll_number","marks","grade",
           "signature","qr","seal","photo","course","academic_year"]

TEXT = (10, 20, 130)
BLACK = (20, 20, 20)
WHITE = (255, 255, 255)


def font(size, bold=False):
    paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
    ]
    for p in paths:
        if Path(p).exists():
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()


def student(i):
    rng = random.Random(SEED + i)
    name = f"{FIRST_NAMES[i % len(FIRST_NAMES)]} {LAST_NAMES[(i * 7) % len(LAST_NAMES)]}"
    cert_id = f"CERT2025{i+1:06d}"
    roll = f"FTU24{(i+1):04d}"
    dept = DEPARTMENTS[i % len(DEPARTMENTS)]
    semester = ["IV","V","VI","VII","VIII"][i % 5]
    year = f"{2024 + (i % 3)}-{2025 + (i % 3)}"
    day = (i % 28) + 1
    month = (i % 12) + 1
    date = f"{day:02d}-{month:02d}-2025"
    rows = []
    points = []
    for j, (code, course, credits) in enumerate(COURSES):
        internal = 20 + ((i * 7 + j * 3) % 11)
        external = 35 + ((i * 11 + j * 5) % 36)
        total = internal + external
        grade, gp = GRADES[(i + j) % len(GRADES)]
        rows.append((code, course, credits, internal, external, total, grade))
        points.append(gp * credits)
    sgpa = round(sum(points) / sum(c for _,_,c,*_ in rows), 2)
    cgpa = round(6.85 + ((i * 37) % 140) / 100, 2)
    return dict(name=name, cert_id=cert_id, roll=roll, dept=dept,
                semester=semester, year=year, date=date, rows=rows,
                sgpa=sgpa, cgpa=cgpa, seed=rng.randint(0, 10**9))


def draw_qr(value, x=1040, y=322, size=120):
    qr = qrcode.QRCode(version=2, box_size=4, border=1)
    qr.add_data(value)
    qr.make(fit=True)
    q = qr.make_image(fill_color="black", back_color="white").convert("RGB")
    return q.resize((size, size), Image.Resampling.NEAREST)


def base_certificate(s):
    img = Image.new("RGB", (W, H), WHITE)
    d = ImageDraw.Draw(img)
    d.rectangle((23,23,W-23,H-23), outline=(20,20,20), width=3)
    d.rounded_rectangle((35,42,W-35,173), radius=12, fill=(235,244,255), outline=(55,110,245), width=2)
    d.ellipse((74,72,170,168), outline=(25,75,170), width=3)
    d.ellipse((88,86,156,154), outline=(25,75,170), width=2)
    d.polygon([(122,96),(151,110),(143,143),(122,157),(101,143),(94,110)], fill=(224,237,255), outline=(130,155,200))
    d.text((197,64),"FUTURETECH UNIVERSITY",fill=(8,28,130),font=font(36,True))
    d.text((198,111),"Autonomous | NAAC A++ | UGC Approved",fill=BLACK,font=font(17))
    d.text((798,168),"ACADEMIC GRADE MEMORANDUM",fill=(10,10,10),font=font(25,True))

    d.rectangle((42,195,1005,628), outline=(155,155,155), width=2)
    labels = [("Certificate ID",s["cert_id"]),("Issue Date",s["date"]),("Student Name",s["name"]),
              ("Roll Number",s["roll"]),("Department",s["dept"]),("Semester",s["semester"]),
              ("Academic Year",s["year"])]
    ys=[228,267,306,345,384,423,462]
    for (lab,val),y in zip(labels,ys):
        d.text((75,y),lab,fill=(15,15,15),font=font(18,True))
        d.text((378,y),":",fill=(15,15,15),font=font(18,True))
        d.text((416,y),val,fill=TEXT,font=font(18))

    q = draw_qr(s["cert_id"]+"|"+s["name"]+"|"+s["roll"])
    d.rectangle((1018,300,1182,464), fill=WHITE, outline=(40,40,40), width=2)
    img.paste(q, (1040,322))
    d.text((1042,462),"QR CODE",fill=(100,100,100),font=font(12))

    d.rectangle((1360,198,1660,528), outline=(70,70,70), width=2)
    d.rectangle((1428,248,1593,493), fill=(255,250,220), outline=(40,40,40), width=2)
    d.ellipse((1480,267,1540,327), fill=(255,190,120), outline=(20,20,20))
    d.rectangle((1460,330,1560,455), fill=(0,105,0))
    d.text((1435,470),s["roll"],fill=(30,30,30),font=font(7))

    x0,y0=42,704
    widths=[105,520,100,98,98,98,98]
    headers=["Course","Subject Name","Credits","Internal","External","Total","Grade"]
    xs=[x0]
    for ww in widths: xs.append(xs[-1]+ww)
    d.rectangle((x0,y0,xs[-1],y0+315), outline=(80,80,80), width=2)
    d.rectangle((x0,y0,xs[-1],y0+45), fill=(220,235,255))
    for x in xs[1:-1]: d.line((x,y0,x,y0+315),fill=(100,100,100),width=1)
    for k,h in enumerate(headers):
        bb=d.textbbox((0,0),h,font=font(13,True))
        d.text(((xs[k]+xs[k+1]-bb[2])/2,y0+14),h,fill=BLACK,font=font(13,True))
    for r,row in enumerate(s["rows"]):
        yy=y0+45+r*45
        d.line((x0,yy,xs[-1],yy),fill=(205,205,205),width=1)
        for k,v in enumerate(row):
            txt=str(v)
            bb=d.textbbox((0,0),txt,font=font(12))
            d.text(((xs[k]+xs[k+1]-bb[2])/2,yy+14),txt,fill=(25,25,25),font=font(12))

    d.line((42,1055,1985,1055),fill=(150,150,150),width=1)
    d.text((70,1090),"SGPA:",fill=(15,15,15),font=font(17,True))
    d.text((160,1090),f"{s['sgpa']:.2f}",fill=(0,100,0),font=font(17,True))
    d.text((375,1090),"CGPA:",fill=(15,15,15),font=font(17,True))
    d.text((465,1090),f"{s['cgpa']:.2f}",fill=(0,100,0),font=font(17,True))

    bx,by=700,1125
    rng=random.Random(s["seed"])
    for j in range(70):
        if rng.random() < .55:
            d.rectangle((bx+j*4,by,bx+j*4+2,by+40),fill=(15,15,15))
    d.text((700,1173),s["cert_id"],fill=(20,20,20),font=font(10))
    d.ellipse((1010,1095,1090,1175),outline=(40,100,230),width=3)
    d.ellipse((1023,1108,1077,1162),outline=(80,130,240),width=1)
    d.text((1000,1188),"OFFICIAL SEAL",fill=(255,0,0),font=font(10,True))
    d.arc((1450,1110,1570,1160),180,350,fill=(60,90,160),width=2)
    d.line((1455,1148,1560,1122),fill=(60,90,160),width=2)
    d.line((1430,1170,1610,1170),fill=(40,40,40),width=1)
    d.text((1450,1183),"Controller of Examinations",fill=(20,20,20),font=font(12,True))
    return img


def alternate_name(s, rng):
    current = s["name"]
    while True:
        candidate = f"{rng.choice(FIRST_NAMES)} {rng.choice(LAST_NAMES)}"
        if candidate != current:
            return candidate


def tamper(img, s, kind):
    out=img.copy()
    d=ImageDraw.Draw(out)
    rng=random.Random(s["seed"] + sum(kind.encode("utf-8")))

    if kind == "name":
        new = alternate_name(s, rng)
        d.rectangle((410,300,930,334), fill=WHITE)
        d.text((416,304),new,fill=TEXT,font=font(18))

    elif kind == "date":
        new=f"{rng.randint(1,28):02d}-{rng.randint(1,12):02d}-{rng.choice([2025,2026,2027])}"
        d.rectangle((410,260,700,294), fill=WHITE)
        d.text((416,265),new,fill=TEXT,font=font(18))

    elif kind == "certificate_id":
        new=f"CERT2025{rng.randint(501,999):06d}"
        d.rectangle((410,220,760,254), fill=WHITE)
        d.text((416,225),new,fill=TEXT,font=font(18))

    elif kind == "roll_number":
        new=f"FTU24{rng.randint(5000,9999):04d}"
        d.rectangle((410,338,760,373), fill=WHITE)
        d.text((416,343),new,fill=TEXT,font=font(18))

    elif kind == "marks":
        row=rng.randrange(6)
        yy=704+45+row*45
        old=str(s["rows"][row][4])
        new=str(min(70, max(35, int(old)+rng.choice([-8,-5,5,7,9]))))
        d.rectangle((865,yy+8,963,yy+38),fill=WHITE)
        bb=d.textbbox((0,0),new,font=font(12))
        d.text(((865+963-bb[2])/2,yy+14),new,fill=(25,25,25),font=font(12))

    elif kind == "grade":
        row=rng.randrange(6)
        yy=704+45+row*45
        old=s["rows"][row][6]
        new=rng.choice([g for g,_ in GRADES if g!=old])
        d.rectangle((1061,yy+8,1158,yy+38),fill=WHITE)
        bb=d.textbbox((0,0),new,font=font(12))
        d.text(((1061+1158-bb[2])/2,yy+14),new,fill=(25,25,25),font=font(12))

    elif kind == "signature":
        d.arc((1450,1112,1575,1158),195,355,fill=(65,95,165),width=2)
        d.line((1455,1144,1568,1120),fill=(65,95,165),width=2)
        d.arc((1490,1100,1540,1150),190,320,fill=(65,95,165),width=2)

    elif kind == "qr":
        new_value=f"{s['cert_id']}|{alternate_name(s,rng)}|{s['roll']}|verification"
        q=draw_qr(new_value)
        d.rectangle((1018,300,1182,464),fill=WHITE,outline=(40,40,40),width=2)
        out.paste(q,(1040,322))

    elif kind == "seal":
        d.ellipse((1010,1095,1090,1175),outline=(45,105,225),width=3)
        d.arc((1020,1105,1080,1165),20,310,fill=(65,115,230),width=1)

    elif kind == "photo":
        d.rectangle((1428,248,1593,493),fill=(255,250,220),outline=(40,40,40),width=2)
        skin=rng.choice([(230,170,120),(205,140,95),(245,190,145)])
        shirt=rng.choice([(20,70,120),(70,60,130),(110,70,40)])
        d.ellipse((1480,267,1540,327),fill=skin,outline=(20,20,20))
        d.rectangle((1460,330,1560,455),fill=shirt)
        d.text((1435,470),s["roll"],fill=(30,30,30),font=font(7))

    elif kind == "course":
        row=rng.randrange(6)
        yy=704+45+row*45
        alternatives=[c for _,c,_ in COURSES if c!=s["rows"][row][1]]
        new=rng.choice(alternatives)
        d.rectangle((147,yy+8,667,yy+38),fill=WHITE)
        bb=d.textbbox((0,0),new,font=font(12))
        d.text(((147+667-bb[2])/2,yy+14),new,fill=(25,25,25),font=font(12))

    elif kind == "academic_year":
        start=rng.choice([2023,2025,2026])
        new=f"{start}-{start+1}"
        d.rectangle((410,462,760,496),fill=WHITE)
        d.text((416,468),new,fill=TEXT,font=font(18))

    return out


def generate(count=500):
    REAL.mkdir(parents=True,exist_ok=True)
    TAMPERED.mkdir(parents=True,exist_ok=True)
    with open(DATASET/"metadata.csv","w",newline="",encoding="utf-8") as f:
        w=csv.writer(f)
        w.writerow(["certificate_id","name","roll_number","department","semester","academic_year","tamper_type","real_file","tampered_file"])
        for i in range(count):
            s=student(i)
            original=base_certificate(s)
            real_name=f"{s['cert_id']}.png"
            tamper_kind=TAMPERS[i % len(TAMPERS)]
            tampered_name=f"{s['cert_id']}__{tamper_kind}.png"
            original.save(REAL/real_name,compress_level=6)
            tamper(original,s,tamper_kind).save(TAMPERED/tampered_name,compress_level=6)
            w.writerow([s["cert_id"],s["name"],s["roll"],s["dept"],s["semester"],s["year"],tamper_kind,real_name,tampered_name])
    print(f"Generated {count} genuine + {count} tampered certificates.")


if __name__=="__main__":
    generate(500)
