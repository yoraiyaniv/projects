from flask import Flask, render_template, request, redirect, url_for, jsonify
import sys
from datetime import datetime
sys.path.append("../")
sys.path.append("/Users/yoraiyaniv/CODE/personal_web_assistant")
from core.db import (
    get_tasks, 
    Task, 
    create_task, 
    Priority, 
    get_objectives, 
    Objective, 
    get_objective_by_id, 
    delete_task,
    update_objective_order,
    update_task_order,
    update_objective,
    get_task_by_id,
    update_task,
    create_objective,
    delete_objective
)

app = Flask(__name__)

@app.route("/")
@app.route("/home")
def home():
    tasks = [Task(t[1], t[2], get_objective_by_id(t[3]), datetime.fromtimestamp(t[4]), Priority(t[5]), t[0]) for t in get_tasks()]
    objectives = [Objective(o[1], o[2], o[3]) for o in get_objectives()]
    return render_template("home.html", tasks=tasks, objectives=objectives)

@app.route("/delete-task/<int:task_id>")
def delete_task_route(task_id):
    delete_task(task_id)
    return redirect(url_for('home'))

@app.route('/add-task', methods=['GET', 'POST'])
def add_task():
    if request.method == 'POST':
        # Get form data
        title = request.form.get('title')
        description = request.form.get('description')
        due_date = request.form.get('due_date')
        objective_name = request.form.get('objective')  # This will now receive the objective ID
        priority = request.form.get('priority')
        
        # Get the objective from database or create a new Objective instance based on your needs
        objective = get_objective_by_id(objective_name)  # You'll need to implement this function
        new_task = Task(title=title, description=description, deadline=datetime.strptime(due_date, "%Y-%m-%d"), objective=objective, priority=Priority(int(priority)))
        create_task(new_task)
        
        return redirect(url_for('home'))
    
    # If GET request, fetch objectives and pass them to the template
    objectives = [Objective(o[1], o[2], o[3]) for o in get_objectives()]
    return render_template('add_task.html', objectives=objectives)

@app.route('/add-objective', methods=['GET', 'POST'])
def add_objective():
    if request.method == 'POST':
        # Get form data
        name = request.form.get('name')
        color = request.form.get('color')
        progress = int(request.form.get('progress', 0))
        
        # Create new objective
        new_objective = Objective(name=name, progress=progress, color=color)
        create_objective(new_objective)
        
        return redirect(url_for('home'))
    
    return render_template('add_objective.html')

@app.route('/edit-task/<int:task_id>', methods=['GET', 'POST'])
def edit_task_route(task_id):
    task = get_task_by_id(task_id)  # You'll need to implement this function
    if request.method == 'POST':
        # Get form data
        title = request.form.get('title')
        description = request.form.get('description')
        due_date = request.form.get('due_date')
        objective_name = request.form.get('objective')
        priority = request.form.get('priority')
        
        # Update task
        objective = get_objective_by_id(objective_name)
        updated_task = Task(
            title=title,
            description=description,
            deadline=datetime.strptime(due_date, "%Y-%m-%d"),
            objective=objective,
            priority=Priority(int(priority)),
            id=task_id
        )
        update_task(updated_task)  # You'll need to implement this function
        
        return redirect(url_for('home'))
    
    objectives = [Objective(o[1], o[2], o[3]) for o in get_objectives()]
    return render_template('edit_task.html', task=task, objectives=objectives)

@app.route('/edit-objective/<objective_name>', methods=['GET', 'POST'])
def edit_objective_route(objective_name):
    objective = get_objective_by_id(objective_name)
    if request.method == 'POST':
        # Get form data
        name = request.form.get('name')
        color = request.form.get('color')
        progress = int(request.form.get('progress', 0))
        
        # Update objective
        updated_objective = Objective(name=name, progress=progress, color=color)
        update_objective(objective.name, updated_objective)  # You'll need to implement this function
        
        return redirect(url_for('home'))
    
    return render_template('edit_objective.html', objective=objective)

@app.route('/update-objective-order', methods=['POST'])
def update_objective_order_route():
    new_order = request.json.get('order', [])
    if new_order:
        update_objective_order(new_order)  # Pass the order to the function
    return jsonify({'success': True})

@app.route('/update-task-order', methods=['POST'])
def update_task_order_route():
    tasks_order = request.json.get('tasks', [])
    if tasks_order:
        update_task_order(tasks_order)
    return jsonify({'success': True})

@app.route('/delete-objective/<objective_name>')
def delete_objective_route(objective_name):
    delete_objective(objective_name)
    return redirect(url_for('home'))

if __name__ == "__main__":
    app.run(debug=True, port=5000, host="0.0.0.0")