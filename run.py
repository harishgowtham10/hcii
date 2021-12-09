import os
from flask import (
    Flask, flash, render_template,
    redirect, request, session, url_for)
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash
if os.path.exists("env.py"):
    import env


app = Flask(__name__)

app.config["MONGO_DBNAME"] = os.environ.get("MONGO_DBNAME")
app.config["MONGO_URI"] = os.environ.get("MONGO_URI")
app.secret_key = os.environ.get("SECRET_KEY")


mongo = PyMongo(app)


@app.route("/")
def index():
    """
    Display index page.
    Returns,
    template: index.html.
    """
    recipe = mongo.db.recipes.find()
    return render_template(
        "index.html", header="Disclaimer",
        subheader="Please Read Before You Proceed", recipes=recipe)


@app.route("/search", methods=["GET", "POST"])
def search():
    search = request.form.get("search")
    recipes = list(mongo.db.recipes.find({"$text": {"$search": search}}))
    return render_template("recipes.html", recipes=recipes)


@app.route("/get_recipes")
def get_recipes():
    """
    Display recipes page.
    Fetch full list of recipes in database
    Returns:
    template: recipes.html.
    """
    recipe = list(mongo.db.recipes.find().sort("_id", -1))
    return render_template(
        "recipes.html", header="Perfect Recipes",
        subheader="for Gluttony & Self Loathing", recipes=recipe)


@app.route("/recipe/<recipe_id>")
def recipe(recipe_id):
    """
    Display recipe page.
    Fetch recipe by database id from
    MongoDB recipes collection.
    Returns:
    template: recipe.html.
    """
    recipes = mongo.db.recipes.find_one({"_id": ObjectId(recipe_id)})
    return render_template("recipe.html", recipes=recipes)


@app.route("/login", methods=["GET", "POST"])
def login():
    """
    Displays login page and allows user to log into account.
    Checks if the email exists in MongoDB chefs collection.
    Informs accountholder if login is successful or not via flash messages.
    Returns:
    template: profile.html if login successful.
    template: login.html if unsuccessful.
    """
    if request.method == "POST":

        user = mongo.db.chefs.find_one(
            {"email": request.form.get("email").lower()})

        if user:

            if check_password_hash(
                    user["password"], request.form.get("password")):
                    session["email"] = request.form.get("email").lower()
                    session["firstName"] = user["firstName"]
                    flash("Welcome back, we've missed you!")
                    return redirect(url_for("profile", chef=["chef"]))
        else:
            flash("Incorrect Email and/or Password")
            return redirect(url_for("login"))

    return render_template(
        "login.html", header="Log In!")


@app.route("/signup", methods=["GET", "POST"])
def signup():
    """
    Displays signup page to guest user and allows account creation.
    Prevents email duplication by checking chefs collection.
    Stores details on MongoDB database in the chefs collection.
    Returns:
    template: redirect to index.html if successful.
    template: signup.html if unsuccessful.
    """
    if request.method == "POST":

        existing_email = mongo.db.chefs.find_one(
            {"email": request.form.get("email").lower()})

        if existing_email:
            flash("This email is already linked to an account!")
            return redirect(url_for("signup"))

        signup = {
            "firstName": request.form.get("firstname"),
            "lastName": request.form.get("lastname"),
            "email": request.form.get("email").lower(),
            "password": generate_password_hash(request.form.get("password"))
        }
        mongo.db.chefs.insert_one(signup)
        session["email"] = request.form.get("email").lower()
        session["firstName"] = request.form.get("firstname")
        flash("Welcome to the Family, {}!".format(
            request.form.get("firstname")))
        return redirect(url_for("index"))

    return render_template("signup.html", header="Create an Account!")


@app.route("/profile", methods=["GET", "POST"])
def profile():
    """
    Displays profile page, retreives session user's firstName from database.
    Show recipes created by account holder.
    Returns:
    template: profile.html if login successful.
    """
    if 'email' in session:
        chef = mongo.db.chefs.find_one(
            {"email": session["email"]})
        recipes = list(
            mongo.db.recipes.find({"created_by": session["email"]}))

        return render_template(
            "profile.html", header="This is Chef Master,",
            chef=chef, recipes=recipes)
    else:
        return redirect(url_for("index"))


@app.route("/logout")
def logout():
    """
    Removes session cookie.
    Shows flash message that logout has been successful.
    Returns:
    template: login.html.
    """
    flash("Cya Later, We'll Miss You!")
    session.pop("email")
    session.pop("firstName")
    return redirect(url_for("login"))


@app.route("/create_recipe", methods=["GET", "POST"])
def create_recipe():
    """
    Allows user to submit a recipe to the website through a form.
    Allows form fields to be sent to the
    MongoDB recipes collection.
    Adds a new entry in to the collections.
    Returns:
    template: create_recipe.html
    template: recipes.html after entires.
    """
    if 'email' in session:
        chef = mongo.db.chefs.find_one(
            {"email": session["email"]})
        if request.method == "POST":
            recipe = {
                "title": request.form.get("title"),
                "description": request.form.get("description"),
                "ingredients": request.form.get("ingredients"),
                "instructions": request.form.get("instructions"),
                "image_url": request.form.get("image_url"),
                "created_by": session["email"],
                "owner": session["firstName"]
            }
            mongo.db.recipes.insert_one(recipe)
            flash("Recipe Successfully Added")
            return redirect(url_for("get_recipes"))
        recipe = mongo.db.recipes.find().sort("title", 1)
        return render_template(
            "create_recipe.html",
            header="What Sweets you got in Mind?", chef=chef, recipes=recipe)
    else:
        return redirect(url_for("index"))


@app.route("/edit_recipe/<edit_id>", methods=["GET", "POST"])
def edit_recipe(edit_id):
    """
    Allows the user to edit their own recipes through a form.
    Checks the recipe ID field in MongoDB to fetch the data.
    Adds any changes made to the entries
    once submitted to the MongoDB collection.
    template: edit_recipe.html.
    template: recipes.html after entires.
    """
    if request.method == "POST":
        recipe = {
            "title": request.form.get("title"),
            "description": request.form.get("description"),
            "ingredients": request.form.get("ingredients"),
            "instructions": request.form.get("instructions"),
            "image_url": request.form.get("image_url"),
            "created_by": session["email"]
        }
        mongo.db.recipes.update({"_id": ObjectId(edit_id)}, recipe)
        flash("Recipe Successfully Updated")
        return redirect(url_for("get_recipes"))

    recipes = mongo.db.recipes.find_one({"_id": ObjectId(edit_id)})
    return render_template("edit_recipe.html", recipes=recipes)


@app.route("/delete_recipe/<edit_id>")
def delete_recipe(edit_id):
    """
    Allows user to delete recipe.
    Deletes recipe from database.
    Returns:
    template: redirects to recipes.html
    """
    mongo.db.recipes.remove({"_id": ObjectId(edit_id)})
    flash("Recipe Successfully Deleted")
    return redirect(url_for("get_recipes"))


@app.errorhandler(404)
def page_not_found(e):
    """
    Custom 404 error page.
    Returns:
    template: redirects to 404.html
    """
    return render_template('404.html'), 404


@app.errorhandler(405)
def page_forbidden(e):
    """
    Custom 403 error page.
    Returns:
    template: redirects to 405.html
    """
    return render_template('405.html'), 405


@app.errorhandler(500)
def internal_error(e):
    """
    Custom 500 error page.
    Returns:
    template: redirects to 500.html
    """
    return render_template('500.html'), 500


if __name__ == "__main__":
    app.run(
            host=os.environ.get("IP", "0.0.0.0"),
            port=int(os.environ.get("PORT", "5000")),
            debug=False)
