from flask import Flask, request, jsonify, redirect, render_template, flash, url_for, session
from flask_session import Session

from db import DBOps
from pydantic_validation import UrlAssignmentInput


app = Flask(__name__)
app.secret_key = 'random_secret_key'  # Required for flashing messages
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

@app.route("/<id>", methods=["GET"])
def redirect_url(id):
    
    db = DBOps()
    db.delete_expired_urls()
    
    try:
        url: str = db.get_assigned_url(id=id)
        db.close_connection()
    except:
        return "The is no url associated with Id '%s'." %(id), 410 
    
    return redirect(url)
    

@app.route("/assign", methods=["POST"])
def assign_url():
    req_data = request.get_json()
    
    if not req_data:
        return jsonify({"error": "No JSON data provided"}), 400

    data = UrlAssignmentInput(**req_data)
    data = data.dict()
    
    url = data.get("url")
    ttl = data.get("ttl")
    
    db = DBOps()
    
    db.delete_expired_urls()
    
    id = db.assign_url_id(url, ttl=ttl)
    
    if not session.get("ids") is None:
        session["ids"].append(id)
    else:
        session["ids"] = []
        session["ids"].append(id)
    db.close_connection()
    
    return id

@app.route("/unassign", methods=["POST"])
def unassign_url():
    data = request.get_json()
    
    if not data:
        return jsonify({"error": "No JSON data provided"}), 400
    
    id = data.get("id")
    
    if session.get("ids") is None:
        return "You didn't create this url.", 403 
    if not id in session["id"]:
        return "You didn't create this url.", 403 
    
    db = DBOps()
    db.delete_expired_urls()
    
    try:
        url: str = db.get_assigned_url(id=id)
    except:
        return "The is no url associated with Id '%s'." %(id), 410 
    delete: bool = db.delete_id(id=id)
    db.close_connection()
    
    if delete:
        session["ids"].remove(id)
        return "Url %s associated with Id %s has been deleted." %(url, id), 200
    else:
        return "The is no url associated with Id '%s'." %(id), 410 
    
# Route for the main page
@app.route('/', methods=['GET', 'POST'])
def home():
    shortened_urls = None
    if request.method == 'POST':
        if 'remove_all' in request.form:
            for id in session["ids"]:
                db = DBOps()
                db.delete_expired_urls()  
                db.delete_id(id=id)
                db.close_connection()
            session["ids"] = []
            flash("All shortened URLs have been removed.")
        elif "assign" in request.form:
            url = request.form["url"] 
            
            db = DBOps()
            db.delete_expired_urls()  
            
            id = db.assign_url_id(url=url)
            db.close_connection()
            
            if not session.get("ids") is None:
                session["ids"].append(id)
            else:
                session["ids"] = [id]
            
            shortened_urls = [f"{request.host_url}{id}" for id in session.get("ids")]

            return render_template('home.html', short_url=f"{request.host_url}{id}", shortened_urls=shortened_urls)
        else:
            url = request.form['url']
                        
            db = DBOps()
            db.delete_expired_urls()
            
            id = url[-int(db.ID_LEN):]
            
            if session.get("ids") is None:
                flash("You didn't create this url.")
                return render_template('home.html', short_url=None, shortened_urls=shortened_urls)
            if not id in session["ids"]:
                flash("You didn't create this url.")
                shortened_urls = [f"{request.host_url}{id}" for id in session.get("ids")]
                return render_template('home.html', short_url=None, shortened_urls=shortened_urls)
            
            try:
                url: str = db.get_assigned_url(id=id)
            except:
                flash("The is no url associated with Id '%s'." %(id))
            delete: bool = db.delete_id(id=id)
            db.close_connection()
            
            if delete:
                session["ids"].remove(id)
                flash(f'Successfully removed the short URL: {f"{request.host_url}{id}"}')
            else:
                flash(f'Error: Short URL {url} not found.')
                
            if session.get("ids") is not None:
                shortened_urls = [f"{request.host_url}{id}" for id in session.get("ids")]
                
            return render_template('home.html', short_url=None, shortened_urls=shortened_urls)
    
    if session.get("ids") is not None:
        shortened_urls = [f"{request.host_url}{id}" for id in session.get("ids")]
    
    return render_template('home.html', short_url=None, shortened_urls=shortened_urls)


if __name__ == "__main__":
    db = DBOps()
    db.delete_table()
    db.create_urls_table()
    db.close_connection()
    app.run(host='0.0.0.0', port=5000,debug=True)