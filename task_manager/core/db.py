import datetime
import psycopg2
import enum
from .models import Task, Priority, Objective

class Priority(enum.Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3


class Objective:
    def __init__(self, name:str, progress:int, color:str):
        self.name = name
        self.progress = progress
        self.color = color
        
        
class Task:
    def __init__(self, title, description, objective, deadline, priority, id=None, position=None):
        self.id = id
        self.title = title
        self.description = description
        self.objective = objective
        self.deadline = deadline
        self.priority = priority
        self.position = position


def connect_to_db():
    try:
        conn = psycopg2.connect(
            host="postgres", # TODO: change to docker container - postgres
            database="tasks",
            user="postgres",
            password="postgres"
        )
        return conn
    except Exception as e:
        print(e)
        raise e

def create_table_tasks():
    conn = connect_to_db()
    cursor = conn.cursor()
    cursor.execute("DROP TABLE IF EXISTS tasks")
    cursor.execute("CREATE TABLE tasks (id SERIAL PRIMARY KEY, title VARCHAR(255), description TEXT, objective TEXT, deadline FLOAT, priority INT)")
    conn.commit()
    conn.close()
    
def create_table_objectives():
    conn = connect_to_db()
    cursor = conn.cursor()
    cursor.execute("DROP TABLE IF EXISTS objectives")
    cursor.execute("CREATE TABLE objectives (id SERIAL PRIMARY KEY, name VARCHAR(255), progress INT, color VARCHAR(255))")
    conn.commit()
    conn.close()

def create_objective(objective):
    conn = connect_to_db()
    cursor = conn.cursor()
    
    try:
        # Get the maximum position
        cursor.execute("""
            SELECT COALESCE(MAX(position) + 1, 0)
            FROM objectives
        """)
        position = cursor.fetchone()[0]
        
        cursor.execute("BEGIN")
        cursor.execute(
            """
            INSERT INTO objectives (name, progress, color, position) 
            VALUES (%s, %s, %s, %s)
            """,
            (objective.name, objective.progress, objective.color, position)
        )
        cursor.execute("COMMIT")
    except Exception as e:
        cursor.execute("ROLLBACK")
        raise e
    finally:
        conn.close()

def create_task(task:Task):
    conn = connect_to_db()
    cursor = conn.cursor()
    
    try:
        # Get the maximum position for the objective
        cursor.execute("""
            SELECT COALESCE(MAX(position) + 1, 0)
            FROM tasks
            WHERE objective = %s
        """, (task.objective.name,))
        position = cursor.fetchone()[0]
        
        cursor.execute("""
            INSERT INTO tasks (title, description, objective, deadline, priority, position) 
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (
            task.title,
            task.description,
            task.objective.name,
            task.deadline.timestamp(),
            task.priority.value,
            position
        ))
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()
    
def get_tasks():
    conn = connect_to_db()
    cursor = conn.cursor()
    
    # First, ensure the position column exists
    cursor.execute("""
        DO $$ 
        BEGIN 
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                          WHERE table_name='tasks' AND column_name='position') THEN
                ALTER TABLE tasks ADD COLUMN position INTEGER;
                -- Initialize positions based on current order
                WITH ranked AS (
                    SELECT id, ROW_NUMBER() OVER (PARTITION BY objective ORDER BY id) - 1 as rn 
                    FROM tasks
                )
                UPDATE tasks 
                SET position = ranked.rn 
                FROM ranked 
                WHERE tasks.id = ranked.id;
            END IF;
        END $$;
    """)
    conn.commit()
    
    # Now we can safely order by position
    cursor.execute("SELECT * FROM tasks ORDER BY objective, COALESCE(position, 999999), id")
    tasks = cursor.fetchall()
    conn.close()
    return tasks

def get_objectives():
    conn = connect_to_db()
    cursor = conn.cursor()
    
    # First, ensure the position column exists
    cursor.execute("""
        DO $$ 
        BEGIN 
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                          WHERE table_name='objectives' AND column_name='position') THEN
                ALTER TABLE objectives ADD COLUMN position INTEGER;
                -- Initialize positions based on current order
                WITH ranked AS (
                    SELECT name, ROW_NUMBER() OVER () - 1 as rn 
                    FROM objectives
                )
                UPDATE objectives 
                SET position = ranked.rn 
                FROM ranked 
                WHERE objectives.name = ranked.name;
            END IF;
        END $$;
    """)
    conn.commit()
    
    # Now we can safely order by position
    cursor.execute("SELECT * FROM objectives ORDER BY COALESCE(position, 999999), name")
    objectives = cursor.fetchall()
    conn.close()
    return objectives

def get_objective_by_id(objective_name):
    """
    Retrieve an objective from the database by its ID
    """
    if not objective_name:
        return None
        
    conn = connect_to_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM objectives WHERE name = '%s'"%(objective_name))
    result = cursor.fetchone()
    conn.close()
    
    if result:
        return Objective(result[1], result[2], result[3])
    return None

def delete_task(task_id):
    conn = connect_to_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM tasks WHERE id = %s"%(task_id))  
    conn.commit()
    conn.close()
    
def get_task_by_id(task_id):
    conn = connect_to_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT * FROM tasks WHERE id = %s", (task_id,))
        task_data = cursor.fetchone()
        
        if task_data:
            # Create and return a Task object
            return Task(
                title=task_data[1],
                description=task_data[2],
                objective=get_objective_by_id(task_data[3]),
                deadline=datetime.date.fromtimestamp(task_data[4]),
                priority=Priority(task_data[5]),
                id=task_data[0]
            )
        return None
    finally:
        conn.close()
    
def update_task(task):
    conn = connect_to_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute("BEGIN")
        cursor.execute(
            """
            UPDATE tasks 
            SET title = %s, 
                description = %s, 
                objective = %s, 
                deadline = %s, 
                priority = %s 
            WHERE id = %s
            """,
            (
                task.title,
                task.description,
                task.objective.name,
                task.deadline.timestamp(),
                task.priority.value,
                task.id
            )
        )
        cursor.execute("COMMIT")
    except Exception as e:
        cursor.execute("ROLLBACK")
        raise e
    finally:
        conn.close()

def update_objective(old_name, objective):
    conn = connect_to_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute("BEGIN")
        
        # Update the objective
        cursor.execute(
            "UPDATE objectives SET name = %s, progress = %s, color = %s WHERE name = %s",
            (objective.name, objective.progress, objective.color, old_name)
        )
        
        # If name changed, update any tasks that reference this objective
        if old_name != objective.name:
            cursor.execute(
                "UPDATE tasks SET objective = %s WHERE objective = %s",
                (objective.name, old_name)
            )
        
        cursor.execute("COMMIT")
    except Exception as e:
        cursor.execute("ROLLBACK")
        raise e
    finally:
        conn.close()
    
def update_objective_order(order):
    conn = connect_to_db()
    cursor = conn.cursor()
    
    try:
        # Begin transaction
        cursor.execute("BEGIN")
        
        # Update positions for each objective
        for index, objective_name in enumerate(order):
            cursor.execute(
                "UPDATE objectives SET position = %s WHERE name = %s",
                (index, objective_name)
            )
        
        cursor.execute("COMMIT")
    except Exception as e:
        cursor.execute("ROLLBACK")
        raise e
    finally:
        conn.close()
    
def update_task_order(tasks_order):
    conn = connect_to_db()
    cursor = conn.cursor()
    
    try:
        # Begin transaction
        cursor.execute("BEGIN")
        
        # Update positions for each task within its objective
        for objective in set(task['objective'] for task in tasks_order):
            objective_tasks = [t for t in tasks_order if t['objective'] == objective]
            for index, task_data in enumerate(objective_tasks):
                cursor.execute(
                    "UPDATE tasks SET position = %s, objective = %s WHERE id = %s",
                    (index, task_data['objective'], task_data['id'])
                )
        
        cursor.execute("COMMIT")
    except Exception as e:
        cursor.execute("ROLLBACK")
        raise e
    finally:
        conn.close()
    
def delete_objective(objective_name):
    conn = connect_to_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute("BEGIN")
        
        # First delete all tasks associated with this objective
        cursor.execute(
            "DELETE FROM tasks WHERE objective = %s",
            (objective_name,)
        )
        
        # Then delete the objective
        cursor.execute(
            "DELETE FROM objectives WHERE name = %s",
            (objective_name,)
        )
        
        # Reorder remaining objectives to prevent gaps
        cursor.execute("""
            WITH ranked AS (
                SELECT name, ROW_NUMBER() OVER (ORDER BY position) - 1 as new_position
                FROM objectives
            )
            UPDATE objectives 
            SET position = ranked.new_position
            FROM ranked 
            WHERE objectives.name = ranked.name
        """)
        
        cursor.execute("COMMIT")
    except Exception as e:
        cursor.execute("ROLLBACK")
        raise e
    finally:
        conn.close()
    