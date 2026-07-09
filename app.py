from flask import Flask, render_template, request, redirect, url_for, session, flash, abort
from db import get_connection
from werkzeug.utils import secure_filename
import os
import uuid

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "change-this-before-production")
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "static", "uploads")
ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png"}
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route("/")
def root(): return redirect(url_for("welcome"))

@app.route("/welcome")
def welcome(): return render_template("welcome.html")

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "GET": return render_template("signup.html")
    name, email, password = (request.form.get(x, "").strip() for x in ("name","email","password"))
    if not name or not email or not password:
        flash("Please complete all fields.", "error"); return redirect(url_for("signup"))
    conn = get_connection(); cur = conn.cursor()
    try:
        cur.execute("INSERT INTO users (name,email,password) VALUES (%s,%s,%s)", (name,email,password))
        conn.commit(); flash("Account created. Please log in.", "success")
        return redirect(url_for("login"))
    except Exception:
        conn.rollback(); flash("This email is already registered.", "error"); return redirect(url_for("signup"))
    finally: cur.close(); conn.close()

@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "GET": return render_template("login.html")
    email, password = request.form.get("email","").strip(), request.form.get("password","")
    conn=get_connection(); cur=conn.cursor()
    cur.execute("SELECT id,name FROM users WHERE email=%s AND password=%s", (email,password))
    user=cur.fetchone(); cur.close(); conn.close()
    if not user: flash("Invalid email or password.", "error"); return redirect(url_for("login"))
    session["user_id"], session["user_name"] = user
    return redirect(url_for("home"))

@app.route("/logout")
def logout(): session.clear(); return redirect(url_for("welcome"))

@app.route("/home")
def home():
    page=max(request.args.get("page",1,type=int),1); limit=6; offset=(page-1)*limit
    conn=get_connection(); cur=conn.cursor()
    cur.execute("""SELECT v.id,v.title,v.price,b.name,
        (SELECT image_path FROM vehicle_images WHERE vehicle_id=v.id ORDER BY id LIMIT 1)
        FROM vehicles v JOIN brands b ON v.brand_id=b.id
        WHERE v.is_deleted=FALSE ORDER BY v.id DESC LIMIT %s OFFSET %s""",(limit,offset))
    vehicles=[{"id":x[0],"title":x[1],"price":x[2],"brand":x[3],"image":x[4]} for x in cur.fetchall()]
    cur.execute("SELECT COUNT(*) FROM vehicles WHERE is_deleted=FALSE"); total=cur.fetchone()[0]
    cur.close(); conn.close()
    return render_template("index.html",vehicles=vehicles,page=page,total_pages=max(1,(total+limit-1)//limit))

@app.route("/add-vehicle", methods=["GET","POST"])
def add_vehicle():
    if "user_id" not in session: return redirect(url_for("login"))
    conn=get_connection(); cur=conn.cursor()
    if request.method=="GET":
        cur.execute("SELECT id,name FROM brands ORDER BY name"); brands=cur.fetchall(); cur.close(); conn.close()
        return render_template("add_vehicle.html",brands=brands)
    try:
        title=request.form.get("title","").strip(); price=float(request.form.get("price","")); year=int(request.form.get("model_year",""))
        brand_id=int(request.form.get("brand_id","")); description=request.form.get("description","").strip()
        if not title or price <= 0 or year < 1900: raise ValueError
        cur.execute("""INSERT INTO vehicles (title,price,model_year,description,brand_id,user_id)
                    VALUES (%s,%s,%s,%s,%s,%s) RETURNING id""",(title,price,year,description,brand_id,session["user_id"]))
        vehicle_id=cur.fetchone()[0]
        for image in request.files.getlist("images"):
            if image and image.filename:
                if not allowed_file(image.filename): raise ValueError("Images must be JPG, JPEG, or PNG.")
                filename=f"{uuid.uuid4()}_{secure_filename(image.filename)}"; image.save(os.path.join(UPLOAD_FOLDER,filename))
                cur.execute("INSERT INTO vehicle_images (vehicle_id,image_path) VALUES (%s,%s)",(vehicle_id,f"static/uploads/{filename}"))
        conn.commit(); flash("Vehicle listing added.", "success"); return redirect(url_for("home"))
    except (ValueError, TypeError):
        conn.rollback(); flash("Check the form values and image format.", "error"); return redirect(url_for("add_vehicle"))
    finally: cur.close(); conn.close()

@app.route("/vehicle/<int:vehicle_id>")
def vehicle_detail(vehicle_id):
    conn=get_connection(); cur=conn.cursor()
    cur.execute("""SELECT v.id,v.title,v.price,v.model_year,v.description,b.name,v.user_id FROM vehicles v
                 JOIN brands b ON v.brand_id=b.id WHERE v.id=%s AND v.is_deleted=FALSE""",(vehicle_id,))
    vehicle=cur.fetchone()
    if not vehicle: cur.close(); conn.close(); abort(404)
    cur.execute("SELECT image_path FROM vehicle_images WHERE vehicle_id=%s ORDER BY id",(vehicle_id,)); images=cur.fetchall()
    cur.close(); conn.close(); return render_template("vehicle_detail.html",vehicle=vehicle,images=images)

@app.post("/delete/<int:vehicle_id>")
def delete_vehicle(vehicle_id):
    if "user_id" not in session: return redirect(url_for("login"))
    conn=get_connection(); cur=conn.cursor()
    cur.execute("UPDATE vehicles SET is_deleted=TRUE WHERE id=%s AND user_id=%s",(vehicle_id,session["user_id"]))
    conn.commit(); changed=cur.rowcount; cur.close(); conn.close()
    flash("Listing deleted." if changed else "You can only delete your own listings.", "success" if changed else "error")
    return redirect(url_for("home"))

if __name__=="__main__": app.run(debug=True)
