import mysql.connector
from flask import Flask, request, jsonify, render_template, redirect, url_for,session
from random import randint
from datetime import datetime
import time

app = Flask(__name__)
app.secret_key = 'ems'

def runQuery(query, params=None):
    try:
        db = mysql.connector.connect(
            host='localhost', 
            database='event', 
            user='root', 
            password='your_password'
        )
        cursor = db.cursor(buffered=True)
        cursor.execute(query, params)
        
        if query.strip().lower().startswith("select"):
            result = cursor.fetchall()
        else:
            db.commit()
            result = []

        return result

    except Exception as e:
        print(f"Database error: {e}")
        return []

    finally:
        db.close()

@app.route('/events_info', methods=['GET', 'POST'])
def renderLoginPage():
    events = runQuery("SELECT * FROM events")
    user_info = session.get('user_info', {})
    

    if request.method == 'POST':
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        email = request.form['e_mail']
        phone_num = request.form['phone_num']
        event_id = request.form['Event']
        ticket_type = request.form['ticket_type']
        payment_type = request.form['payment_type']
        

        
        if len(phone_num) != 10 or not phone_num.isdigit():
            return render_template('loginfail.html', user_info=user_info, errors=["Invalid Phone Number!"])

        
        if not email.endswith('.com'):
            return render_template('loginfail.html', user_info=user_info, errors=["Invalid Email!"])

        try:
            
            runQuery("INSERT INTO Customer (first_name, last_name, e_mail, phone_num) VALUES (%s, %s, %s, %s)",
                     (first_name, last_name, email, phone_num))
            
            
            customer_id = runQuery("SELECT ID FROM Customer WHERE e_mail = %s", (email,))[0][0]

            
            company_id = runQuery("SELECT company_id FROM events WHERE ID = %s", (event_id,))[0][0]

            
            runQuery("INSERT INTO cust_of (company_id, customer_id) VALUES (%s, %s)", (company_id, customer_id))

            
            event = runQuery("SELECT general_price, vip_price FROM events WHERE ID = %s", (event_id,))[0]
            if ticket_type == 'General':
                price = event[0]
            else:
                price = event[1]

            
            distributor_id = randint(1, 24)

            
            runQuery("INSERT INTO TICKET (type, tickets_available, tickets_sold, price, event_id, distributer_id) VALUES (%s, %s, %s, %s, %s, %s)",
                     (ticket_type, 100, 1, price, event_id, distributor_id))

            
            ticket_id = runQuery("SELECT ID FROM TICKET ORDER BY ID DESC LIMIT 1")[0][0]

            
            runQuery("INSERT INTO Purchase (customer_id, ticket_id, payment_type, purchase_date) VALUES (%s, %s, %s, %s)",
                     (customer_id, ticket_id, payment_type, datetime.now()))
            

        except Exception as e:
            print(f"Error: {str(e)}")
            
            return render_template('loginfail.html', errors=["Database error: " + str(e)])
        event_type_popularity = runQuery("""
        SELECT 
            E.type AS EventType, 
            COUNT(T.event_id) AS TotalTicketsSold
        FROM 
            events E
        JOIN 
            TICKET T ON E.ID = T.event_id
        GROUP BY 
            E.type
        ORDER BY 
            TotalTicketsSold DESC;
    """)
        
        return render_template('index.html', events=events, user_info=user_info, errors=["Successfully Registered!"],event_type_popularity=event_type_popularity)
    
    user_id = session.get('ID')
        

    query = "SELECT first_name, last_name, e_mail, phone_num FROM Customer WHERE ID = %s"
    params = (user_id,)
    result = runQuery(query, params)
    if result:
            user_info = {
                'first_name': result[0][0],
                'last_name': result[0][1],
                'e_mail': result[0][2],
                'phone_num': result[0][3]
            }
    else:
            user_info = {
                'first_name': '',
                'last_name': '',
                'e_mail': '',
                'phone_num': ''
            }
            
    event_type_popularity = runQuery("""
        SELECT 
            E.type AS EventType, 
            COUNT(T.event_id) AS TotalTicketsSold
        FROM 
            events E
        JOIN 
            TICKET T ON E.ID = T.event_id
        GROUP BY 
            E.type
        ORDER BY 
            TotalTicketsSold DESC;
    """)

    events = runQuery("SELECT * FROM events")
    return render_template('events_info.html',user_info=user_info, events=events, event_type_popularity=event_type_popularity)


    

@app.route('/')
def events_info():
    if request.method == 'POST':
        try:
            if 'newEvent' in request.form:
                Name = request.form["newEvent"]
                fee = request.form["Fee"]
                
                Type = request.form["EventType"]
                Location = request.form["EventLocation"]
                Date = request.form['Date']
            elif 'EventId' in request.form:
                EventId = request.form["EventId"]
                runQuery("DELETE FROM events WHERE event_id=%s", (EventId,))
        except mysql.connector.Error as e:
            print(f"Error: {e}")
    
    event_type_popularity = runQuery("""
        SELECT 
            E.type AS EventType, 
            COUNT(T.event_id) AS TotalTicketsSold
        FROM 
            events E
        JOIN 
            TICKET T ON E.ID = T.event_id
        GROUP BY 
            E.type
        ORDER BY 
            TotalTicketsSold DESC;
    """)

    events = runQuery("SELECT * FROM events")
    return render_template('index.html', events=events, event_type_popularity=event_type_popularity)




@app.route('/loginfail', methods=['GET'])
def renderLoginFail():
    return render_template('loginfail.html')

@app.route('/admin', methods=['GET', 'POST'])
def renderAdmin():
    if request.method == 'POST':
        UN = request.form['username']
        PS = request.form['password']
        print(f"Received Username: {UN}")  
        print(f"Received Password: {PS}") 
        if UN == 'admin' and PS == 'admin':
            session['logged_in'] = True
            return redirect('/eventType')
        elif UN == 'manager' and PS == 'manager':
            session['logged_in'] = True
            return redirect('/manager')
        else:
        
            query = "SELECT ID FROM Customer WHERE e_mail = %s AND phone_num = %s"
            params = (UN, PS)
            result = runQuery(query, params)
            if result:
             
                session['logged_in'] = True
                session['ID'] = result[0][0] 
                return redirect('/')

        return render_template('admin.html', errors=["Wrong Username/Password"])

    return render_template('admin.html')


@app.route('/logout', methods=['GET'])
def logout():
    session.clear()
    return redirect('/')

@app.route('/customer_dashboard', methods=['GET', 'POST'])
def customerDashboard():
    if request.method == 'POST':
        user_id = session.get('ID')
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        e_mail = request.form['e_mail']
        phone_num = request.form['phone_num']

        update_query = """
        UPDATE Customer 
        SET first_name = %s, last_name = %s, e_mail = %s, phone_num = %s 
        WHERE ID = %s
        """
        params = (first_name, last_name, e_mail, phone_num, user_id)
        runQuery(update_query, params)

        session['first_name'] = first_name
        session['last_name'] = last_name
        session['e_mail'] = e_mail
        session['phone_num'] = phone_num

        return redirect('/')

    elif request.method == 'GET':
        user_id = session.get('ID')
        if not user_id:
            return redirect('/admin') 

        query = "SELECT first_name, last_name, e_mail, phone_num FROM Customer WHERE ID = %s"
        params = (user_id,)
        result = runQuery(query, params)
        if result:
            user_info = {
                'first_name': result[0][0],
                'last_name': result[0][1],
                'e_mail': result[0][2],
                'phone_num': result[0][3]
            }
        else:
            user_info = {
                'first_name': '',
                'last_name': '',
                'e_mail': '',
                'phone_num': ''
            }
    
    return render_template('customer_dashboard.html', user_info=user_info)




@app.route('/eventType', methods=['GET', 'POST'])
def getEvents():
    if request.method == 'POST':
        try:
            if 'newEvent' in request.form:
                Name = request.form["newEvent"]
                fee = request.form["Fee"]
                Type = request.form["EventType"]
                Location = request.form["EventLocation"]
                Date = request.form['Date']
            elif 'EventId' in request.form:
                EventId = request.form["EventId"]
                runQuery("DELETE FROM events WHERE event_id=%s", (EventId,))
        except mysql.connector.Error as e:
            print(f"Error: {e}")

    most_spending_customer = runQuery("""
        SELECT 
    C.ID AS CustomerID, 
    CONCAT(C.first_name, ' ', C.last_name) AS CustomerName,
    SUM(
        CASE
            WHEN T.type = 'vip' THEN E.vip_price
            ELSE E.general_price
        END
    ) AS TotalSpent
FROM 
    Purchase P
JOIN 
    TICKET T ON P.ticket_id = T.ID
JOIN 
    events E ON T.event_id = E.ID
JOIN 
    Customer C ON P.customer_id = C.ID
GROUP BY 
    C.ID, CustomerName
ORDER BY 
    TotalSpent DESC
LIMIT 1;

    """)
    
   
    top_revenue_events = runQuery("""
        SELECT
            ID,
            name AS EventName,
            CAST(income AS DECIMAL) AS TotalRevenue
        FROM 
            events
        ORDER BY 
            TotalRevenue DESC;
    """)
    
 
    company_most_event_types = runQuery("""
        SELECT 
            C.ID AS CompanyID, 
            C.Name AS CompanyName, 
            COUNT(E.type) AS EventTypeCount
        FROM 
            Company C
        JOIN 
            events E ON C.ID = E.company_id
        GROUP BY 
            C.ID, CompanyName
        ORDER BY 
            EventTypeCount DESC
        LIMIT 1;
    """)
    

    company_most_customers = runQuery("""
    SELECT 
        C.ID AS CompanyID,
        C.Name AS CompanyName,
        COUNT(T.event_id) AS TotalTicketsSold
    FROM 
        Company C
    JOIN 
        events E ON C.ID = E.company_id
    JOIN 
        TICKET T ON E.ID = T.event_id
    GROUP BY 
        C.ID, CompanyName
    ORDER BY 
        TotalTicketsSold DESC
    LIMIT 1;
""")
    

    company_sales_ranking = runQuery("""
    SELECT 
        C.ID AS CompanyID,
        C.Name AS CompanyName,
        SUM(CAST(E.income AS DECIMAL)) AS TotalRevenue
    FROM 
        Company C
    LEFT JOIN 
        events E ON C.ID = E.company_id
    GROUP BY 
        C.ID, CompanyName
    ORDER BY 
        TotalRevenue DESC;
""")
    

    customer_loyalty = runQuery("""
        SELECT 
            C.ID AS CustomerID, 
            CONCAT(C.first_name, ' ', C.last_name) AS CustomerName,
            Co.ID AS CompanyID,
            Co.Name AS CompanyName,
            COUNT(P.purchase_id) AS PurchaseCount
        FROM 
            Purchase P
        JOIN 
            Customer C ON P.customer_id = C.ID
        JOIN 
            TICKET T ON P.ticket_id = T.ID
        JOIN 
            events E ON T.event_id = E.ID
        JOIN 
            Company Co ON E.company_id = Co.ID
        GROUP BY 
            C.ID, CustomerName, Co.ID, CompanyName
        ORDER BY 
            CustomerID, CompanyID;
    """)

    event_type_popularity = runQuery("""
        SELECT 
            E.type AS EventType, 
            COUNT(T.event_id) AS TotalTicketsSold
        FROM 
            events E
        JOIN 
            TICKET T ON E.ID = T.event_id
        GROUP BY 
            E.type
        ORDER BY 
            TotalTicketsSold DESC;
    """)

    events = runQuery("SELECT * FROM events")
    companies = runQuery("SELECT * FROM Company")
    distributers = runQuery("SELECT * FROM Distributer")
    customers = runQuery("SELECT * FROM Customer")
    tickets = runQuery("SELECT ID, type, price, event_id, distributer_id FROM Ticket")
    purchases = runQuery("SELECT * FROM Purchase")
    cust_of = runQuery("SELECT * FROM cust_of")
    return render_template('events.html',events=events, companies=companies, distributers=distributers, customers=customers, tickets=tickets, purchases=purchases, cust_of=cust_of, most_spending_customer=most_spending_customer, top_revenue_events=top_revenue_events, company_most_event_types=company_most_event_types, company_most_customers=company_most_customers, company_sales_ranking=company_sales_ranking, customer_loyalty=customer_loyalty, event_type_popularity=event_type_popularity)


    

@app.route('/manager')
def manager():
    if request.method == 'POST':
        try:
            if 'newEvent' in request.form:
                Name = request.form["newEvent"]
                fee = request.form["Fee"]
             
                Type = request.form["EventType"]
                Location = request.form["EventLocation"]
                Date = request.form['Date']
            elif 'EventId' in request.form:
                EventId = request.form["EventId"]
                runQuery("DELETE FROM events WHERE event_id=%s", (EventId,))
        except mysql.connector.Error as e:
            print(f"Error: {e}")


    top_revenue_events = runQuery("""
        SELECT 
            name AS EventName,
            CAST(income AS DECIMAL) AS TotalRevenue
        FROM 
            events
        ORDER BY 
            TotalRevenue DESC;
    """)

    company_most_event_types = runQuery("""
        SELECT 
            C.ID AS CompanyID, 
            C.Name AS CompanyName, 
            COUNT(E.type) AS EventTypeCount
        FROM 
            Company C
        JOIN 
            events E ON C.ID = E.company_id
        GROUP BY 
            C.ID, CompanyName
        ORDER BY 
            EventTypeCount DESC
        LIMIT 1;
    """)
    

    company_sales_ranking = runQuery("""
    SELECT 
        C.ID AS CompanyID,
        C.Name AS CompanyName,
        SUM(CAST(E.income AS DECIMAL)) AS TotalRevenue
    FROM 
        Company C
    LEFT JOIN 
        events E ON C.ID = E.company_id
    GROUP BY 
        C.ID, CompanyName
    ORDER BY 
        TotalRevenue DESC;
""")

    customer_loyalty = runQuery("""
        SELECT 
            C.ID AS CustomerID, 
            CONCAT(C.first_name, ' ', C.last_name) AS CustomerName,
            Co.ID AS CompanyID,
            Co.Name AS CompanyName,
            COUNT(P.purchase_id) AS PurchaseCount
        FROM 
            Purchase P
        JOIN 
            Customer C ON P.customer_id = C.ID
        JOIN 
            TICKET T ON P.ticket_id = T.ID
        JOIN 
            events E ON T.event_id = E.ID
        JOIN 
            Company Co ON E.company_id = Co.ID
        GROUP BY 
            C.ID, CustomerName, Co.ID, CompanyName
        ORDER BY 
            CustomerID, CompanyID;
    """)
  
    event_type_popularity = runQuery("""
        SELECT 
            E.type AS EventType, 
            COUNT(T.event_id) AS TotalTicketsSold
        FROM 
            events E
        JOIN 
            TICKET T ON E.ID = T.event_id
        GROUP BY 
            E.type
        ORDER BY 
            TotalTicketsSold DESC;
    """)
    events = runQuery("SELECT e.ID,e.name,e.type,e.location,e.datetime,e.general_price,e.vip_price,e.income,e.expense,e.details,c.name AS company_name FROM events e JOIN Company c ON e.company_id = c.ID;")
    distributers = runQuery("SELECT * FROM Distributer")
    return render_template('manager.html', events=events,distributers=distributers, top_revenue_events=top_revenue_events, company_most_event_types=company_most_event_types, company_sales_ranking=company_sales_ranking, customer_loyalty=customer_loyalty, event_type_popularity=event_type_popularity)


@app.route('/manage_distributers', methods=['GET', 'POST'])
def manage_distributers():
    if request.method == "POST":
        if 'ID' in request.form and 'name' in request.form  and 'location' in request.form:
            try:
                distributer_id = request.form["ID"]
                name = request.form["name"]
                location = request.form["location"]
                
                runQuery("INSERT INTO Distributer (ID, name, location) VALUES (%s, %s, %s)", (distributer_id, name, location))
                print(f"Distributer added: {distributer_id}, {name}")
                
            except Exception as e:
                print(f"Error adding distributer: {e}")

        elif 'DistributerId' in request.form and 'property' in request.form and 'new_value' in request.form:
            try:
                distributer_id = request.form["DistributerId"]
                property = request.form["property"]
                new_value = request.form["new_value"]

                
                if property in ["ID"]:
                    new_value = new_value.replace(",", "").replace("$", "")
                    new_value = float(new_value) 
                else:
                    new_value = f"'{new_value}'"

                query = f"UPDATE Distributer SET {property} = {new_value} WHERE ID = {distributer_id}"
                runQuery(query)
                print(f"Distributer updated: ID = {distributer_id}, {property} = {new_value}")
            except Exception as e:
                print(f"Error updating company: {e}")
        
        elif 'DistributerID' in request.form:
            try:
                distributer_id = request.form["DistributerID"]
                runQuery("DELETE FROM Distributer WHERE ID = %s", (distributer_id,))
                print(f"Distributer deleted: {distributer_id}")
            except Exception as e:
                print(f"Error deleting distributer: {e}")
    most_spending_customer = runQuery("""
        SELECT 
            C.ID AS CustomerID, 
            CONCAT(C.first_name, ' ', C.last_name) AS CustomerName,
            SUM(T.price) * COUNT(P.purchase_id) AS TotalSpent
        FROM 
            Purchase P
        JOIN 
            TICKET T ON P.ticket_id = T.ID
        JOIN 
            Customer C ON P.customer_id = C.ID
        GROUP BY 
            C.ID, CustomerName
        ORDER BY 
            TotalSpent DESC
        LIMIT 1;
    """)

    top_revenue_events = runQuery("""
        SELECT
            ID,
            name AS EventName,
            CAST(income AS DECIMAL) AS TotalRevenue
        FROM 
            events
        ORDER BY 
            TotalRevenue DESC;
    """)

    company_most_event_types = runQuery("""
        SELECT 
            C.ID AS CompanyID, 
            C.Name AS CompanyName, 
            COUNT(E.type) AS EventTypeCount
        FROM 
            Company C
        JOIN 
            events E ON C.ID = E.company_id
        GROUP BY 
            C.ID, CompanyName
        ORDER BY 
            EventTypeCount DESC
        LIMIT 1;
    """)

    company_most_customers = runQuery("""
    SELECT 
        C.ID AS CompanyID,
        C.Name AS CompanyName,
        COUNT(T.event_id) AS TotalTicketsSold
    FROM 
        Company C
    JOIN 
        events E ON C.ID = E.company_id
    JOIN 
        TICKET T ON E.ID = T.event_id
    GROUP BY 
        C.ID, CompanyName
    ORDER BY 
        TotalTicketsSold DESC
    LIMIT 1;
""")

    company_sales_ranking = runQuery("""
    SELECT 
        C.ID AS CompanyID,
        C.Name AS CompanyName,
        SUM(CAST(E.income AS DECIMAL)) AS TotalRevenue
    FROM 
        Company C
    LEFT JOIN 
        events E ON C.ID = E.company_id
    GROUP BY 
        C.ID, CompanyName
    ORDER BY 
        TotalRevenue DESC;
""")

    customer_loyalty = runQuery("""
        SELECT 
            C.ID AS CustomerID, 
            CONCAT(C.first_name, ' ', C.last_name) AS CustomerName,
            Co.ID AS CompanyID,
            Co.Name AS CompanyName,
            COUNT(P.purchase_id) AS PurchaseCount
        FROM 
            Purchase P
        JOIN 
            Customer C ON P.customer_id = C.ID
        JOIN 
            TICKET T ON P.ticket_id = T.ID
        JOIN 
            events E ON T.event_id = E.ID
        JOIN 
            Company Co ON E.company_id = Co.ID
        GROUP BY 
            C.ID, CustomerName, Co.ID, CompanyName
        ORDER BY 
            CustomerID, CompanyID;
    """)

    event_type_popularity = runQuery("""
        SELECT 
            E.type AS EventType, 
            COUNT(T.event_id) AS TotalTicketsSold
        FROM 
            events E
        JOIN 
            TICKET T ON E.ID = T.event_id
        GROUP BY 
            E.type
        ORDER BY 
            TotalTicketsSold DESC;
    """)
    events = runQuery("SELECT * FROM events")
    companies = runQuery("SELECT * FROM Company")
    distributers = runQuery("SELECT * FROM Distributer")
    customers = runQuery("SELECT * FROM Customer")
    tickets = runQuery("SELECT * FROM Ticket")
    purchases = runQuery("SELECT * FROM Purchase")
    cust_of = runQuery("SELECT * FROM cust_of")

    return render_template('events.html', events=events, companies=companies, distributers=distributers, customers=customers, tickets=tickets, purchases=purchases, cust_of=cust_of, most_spending_customer=most_spending_customer, top_revenue_events=top_revenue_events, company_most_event_types=company_most_event_types, company_most_customers=company_most_customers, company_sales_ranking=company_sales_ranking, customer_loyalty=customer_loyalty, event_type_popularity=event_type_popularity)

@app.route('/manage_distributer_manager', methods=['GET', 'POST'])
def manage_distributer_manager():
    if request.method == "POST":
        if 'ID' in request.form and 'name' in request.form  and 'location' in request.form:
            try:
                distributer_id = request.form["ID"]
                name = request.form["name"]
                location = request.form["location"]
                
                runQuery("INSERT INTO Distributer (ID, name, location) VALUES (%s, %s, %s)", (distributer_id, name, location))
                print(f"Distributer added: {distributer_id}, {name}")
                
            except Exception as e:
                print(f"Error adding distributer: {e}")

        elif 'DistributerId' in request.form and 'property' in request.form and 'new_value' in request.form:
            try:
                distributer_id = request.form["DistributerId"]
                property = request.form["property"]
                new_value = request.form["new_value"]
                
                if property in ["ID"]:
                    new_value = new_value.replace(",", "").replace("$", "")
                    new_value = float(new_value) 
                else:
                    new_value = f"'{new_value}'"

                query = f"UPDATE Distributer SET {property} = {new_value} WHERE ID = {distributer_id}"
                runQuery(query)
                print(f"Distributer updated: ID = {distributer_id}, {property} = {new_value}")
            except Exception as e:
                print(f"Error updating company: {e}")
        
        elif 'DistributerID' in request.form:
            try:
                distributer_id = request.form["DistributerID"]
                runQuery("DELETE FROM Distributer WHERE ID = %s", (distributer_id,))
                print(f"Distributer deleted: {distributer_id}")
            except Exception as e:
                print(f"Error deleting distributer: {e}")
    
    top_revenue_events = runQuery("""
        SELECT 
            name AS EventName,
            CAST(income AS DECIMAL) AS TotalRevenue
        FROM 
            events
        ORDER BY 
            TotalRevenue DESC;
    """)
    
 
    company_most_event_types = runQuery("""
        SELECT 
            C.ID AS CompanyID, 
            C.Name AS CompanyName, 
            COUNT(E.type) AS EventTypeCount
        FROM 
            Company C
        JOIN 
            events E ON C.ID = E.company_id
        GROUP BY 
            C.ID, CompanyName
        ORDER BY 
            EventTypeCount DESC
        LIMIT 1;
    """)
    
    
    

    company_sales_ranking = runQuery("""
    SELECT 
        C.ID AS CompanyID,
        C.Name AS CompanyName,
        SUM(CAST(E.income AS DECIMAL)) AS TotalRevenue
    FROM 
        Company C
    LEFT JOIN 
        events E ON C.ID = E.company_id
    GROUP BY 
        C.ID, CompanyName
    ORDER BY 
        TotalRevenue DESC;
""")
    

    customer_loyalty = runQuery("""
        SELECT 
            C.ID AS CustomerID, 
            CONCAT(C.first_name, ' ', C.last_name) AS CustomerName,
            Co.ID AS CompanyID,
            Co.Name AS CompanyName,
            COUNT(P.purchase_id) AS PurchaseCount
        FROM 
            Purchase P
        JOIN 
            Customer C ON P.customer_id = C.ID
        JOIN 
            TICKET T ON P.ticket_id = T.ID
        JOIN 
            events E ON T.event_id = E.ID
        JOIN 
            Company Co ON E.company_id = Co.ID
        GROUP BY 
            C.ID, CustomerName, Co.ID, CompanyName
        ORDER BY 
            CustomerID, CompanyID;
    """)
    
 
    event_type_popularity = runQuery("""
        SELECT 
            E.type AS EventType, 
            COUNT(T.event_id) AS TotalTicketsSold
        FROM 
            events E
        JOIN 
            TICKET T ON E.ID = T.event_id
        GROUP BY 
            E.type
        ORDER BY 
            TotalTicketsSold DESC;
    """)
    events = runQuery("SELECT e.ID,e.name,e.type,e.location,e.datetime,e.general_price,e.vip_price,e.income,e.expense,e.details,c.name AS company_name FROM events e JOIN Company c ON e.company_id = c.ID;")
    companies = runQuery("SELECT * FROM Company")
    distributers = runQuery("SELECT * FROM Distributer")
    customers = runQuery("SELECT * FROM Customer")
    tickets = runQuery("SELECT * FROM Ticket")
    purchases = runQuery("SELECT * FROM Purchase")
    cust_of = runQuery("SELECT * FROM cust_of")

    return render_template('manager.html', events=events, companies=companies, distributers=distributers, customers=customers, tickets=tickets, purchases=purchases, cust_of=cust_of, top_revenue_events=top_revenue_events, company_most_event_types=company_most_event_types, company_sales_ranking=company_sales_ranking, customer_loyalty=customer_loyalty, event_type_popularity=event_type_popularity)

@app.route('/manage_customers', methods=['GET', 'POST'])
def manage_customers():
    if request.method == "POST":
        if 'ID' in request.form and 'first_name' in request.form  and 'last_name' in request.form and 'e_mail' in request.form and 'phone_num' in request.form:
            try:
                customer_id = request.form["ID"]
                first_name = request.form["first_name"]
                last_name = request.form["last_name"]
                e_mail = request.form["e_mail"]
                phone_num = request.form["phone_num"]

                runQuery("INSERT INTO Customer (ID, first_name, last_name, e_mail, phone_num) VALUES (%s, %s, %s, %s, %s)", (customer_id, first_name, last_name, e_mail, phone_num))
                print(f"Customer added: {customer_id}, {first_name}, {last_name}")
                
            except Exception as e:
                print(f"Error adding customer: {e}")

        
        
        elif 'CustomerID' in request.form:
            try:
                customer_id = request.form["CustomerID"]
                runQuery("DELETE FROM Customer WHERE ID = %s", (customer_id,))
                print(f"Customer deleted: {customer_id}")
            except Exception as e:
                print(f"Error deleting Customer: {e}")
   
    most_spending_customer = runQuery("""
        SELECT 
            C.ID AS CustomerID, 
            CONCAT(C.first_name, ' ', C.last_name) AS CustomerName,
            SUM(T.price) * COUNT(P.purchase_id) AS TotalSpent
        FROM 
            Purchase P
        JOIN 
            TICKET T ON P.ticket_id = T.ID
        JOIN 
            Customer C ON P.customer_id = C.ID
        GROUP BY 
            C.ID, CustomerName
        ORDER BY 
            TotalSpent DESC
        LIMIT 1;
    """)
    

    top_revenue_events = runQuery("""
        SELECT
            ID,
            name AS EventName,
            CAST(income AS DECIMAL) AS TotalRevenue
        FROM 
            events
        ORDER BY 
            TotalRevenue DESC;
    """)
    

    company_most_event_types = runQuery("""
        SELECT 
            C.ID AS CompanyID, 
            C.Name AS CompanyName, 
            COUNT(E.type) AS EventTypeCount
        FROM 
            Company C
        JOIN 
            events E ON C.ID = E.company_id
        GROUP BY 
            C.ID, CompanyName
        ORDER BY 
            EventTypeCount DESC
        LIMIT 1;
    """)

    company_most_customers = runQuery("""
    SELECT 
        C.ID AS CompanyID,
        C.Name AS CompanyName,
        COUNT(T.event_id) AS TotalTicketsSold
    FROM 
        Company C
    JOIN 
        events E ON C.ID = E.company_id
    JOIN 
        TICKET T ON E.ID = T.event_id
    GROUP BY 
        C.ID, CompanyName
    ORDER BY 
        TotalTicketsSold DESC
    LIMIT 1;
""")

    company_sales_ranking = runQuery("""
    SELECT 
        C.ID AS CompanyID,
        C.Name AS CompanyName,
        SUM(CAST(E.income AS DECIMAL)) AS TotalRevenue
    FROM 
        Company C
    LEFT JOIN 
        events E ON C.ID = E.company_id
    GROUP BY 
        C.ID, CompanyName
    ORDER BY 
        TotalRevenue DESC;
""")

    customer_loyalty = runQuery("""
        SELECT 
            C.ID AS CustomerID, 
            CONCAT(C.first_name, ' ', C.last_name) AS CustomerName,
            Co.ID AS CompanyID,
            Co.Name AS CompanyName,
            COUNT(P.purchase_id) AS PurchaseCount
        FROM 
            Purchase P
        JOIN 
            Customer C ON P.customer_id = C.ID
        JOIN 
            TICKET T ON P.ticket_id = T.ID
        JOIN 
            events E ON T.event_id = E.ID
        JOIN 
            Company Co ON E.company_id = Co.ID
        GROUP BY 
            C.ID, CustomerName, Co.ID, CompanyName
        ORDER BY 
            CustomerID, CompanyID;
    """)

    event_type_popularity = runQuery("""
        SELECT 
            E.type AS EventType, 
            COUNT(T.event_id) AS TotalTicketsSold
        FROM 
            events E
        JOIN 
            TICKET T ON E.ID = T.event_id
        GROUP BY 
            E.type
        ORDER BY 
            TotalTicketsSold DESC;
    """)
    events = runQuery("SELECT * FROM events")
    companies = runQuery("SELECT * FROM Company")
    distributers = runQuery("SELECT * FROM Distributer")
    customers = runQuery("SELECT * FROM Customer")
    tickets = runQuery("SELECT * FROM Ticket")
    purchases = runQuery("SELECT * FROM Purchase")
    cust_of = runQuery("SELECT * FROM cust_of")

    return render_template('events.html', events=events, companies=companies, distributers=distributers, customers=customers, tickets=tickets, purchases=purchases, cust_of=cust_of, most_spending_customer=most_spending_customer, top_revenue_events=top_revenue_events, company_most_event_types=company_most_event_types, company_most_customers=company_most_customers, company_sales_ranking=company_sales_ranking, customer_loyalty=customer_loyalty, event_type_popularity=event_type_popularity)

@app.route('/manage_companies', methods=['GET', 'POST'])
def manage_companies():
    if request.method == "POST":
        if 'ID' in request.form and 'name' in request.form  and 'location' in request.form:
            try:
                company_id = request.form["ID"]
                name = request.form["name"]
                location = request.form["location"]
                
                runQuery("INSERT INTO Company (ID, name, location) VALUES (%s, %s, %s)", (company_id, name, location))
                print(f"Company added: {company_id}, {name}")
                
            except Exception as e:
                print(f"Error adding event: {e}")
        
        elif 'CompanyId' in request.form and 'property' in request.form and 'new_value' in request.form:
            try:
                company_id = request.form["CompanyId"]
                property = request.form["property"]
                new_value = request.form["new_value"]
                
                if property in ["ID"]:

                    new_value = new_value.replace(",", "").replace("$", "")
                    new_value = float(new_value)  
                else:
                    new_value = f"'{new_value}'"

                query = f"UPDATE Company SET {property} = {new_value} WHERE ID = {company_id}"
                runQuery(query)
                print(f"Company updated: ID = {company_id}, {property} = {new_value}")
            except Exception as e:
                print(f"Error updating company: {e}")
        
        elif 'CompanyID' in request.form:
            try:
                company_id = request.form["CompanyID"]
                runQuery("DELETE FROM Company WHERE ID = %s", (company_id,))
                print(f"Company deleted: {company_id}")
            except Exception as e:
                print(f"Error deleting event: {e}")
    most_spending_customer = runQuery("""
        SELECT 
            C.ID AS CustomerID, 
            CONCAT(C.first_name, ' ', C.last_name) AS CustomerName,
            SUM(T.price) * COUNT(P.purchase_id) AS TotalSpent
        FROM 
            Purchase P
        JOIN 
            TICKET T ON P.ticket_id = T.ID
        JOIN 
            Customer C ON P.customer_id = C.ID
        GROUP BY 
            C.ID, CustomerName
        ORDER BY 
            TotalSpent DESC
        LIMIT 1;
    """)

    top_revenue_events = runQuery("""
        SELECT
            ID,
            name AS EventName,
            CAST(income AS DECIMAL) AS TotalRevenue
        FROM 
            events
        ORDER BY 
            TotalRevenue DESC;
    """)
    

    company_most_event_types = runQuery("""
        SELECT 
            C.ID AS CompanyID, 
            C.Name AS CompanyName, 
            COUNT(E.type) AS EventTypeCount
        FROM 
            Company C
        JOIN 
            events E ON C.ID = E.company_id
        GROUP BY 
            C.ID, CompanyName
        ORDER BY 
            EventTypeCount DESC
        LIMIT 1;
    """)
    
    company_most_customers = runQuery("""
    SELECT 
        C.ID AS CompanyID,
        C.Name AS CompanyName,
        COUNT(T.event_id) AS TotalTicketsSold
    FROM 
        Company C
    JOIN 
        events E ON C.ID = E.company_id
    JOIN 
        TICKET T ON E.ID = T.event_id
    GROUP BY 
        C.ID, CompanyName
    ORDER BY 
        TotalTicketsSold DESC
    LIMIT 1;
""")
    

    company_sales_ranking = runQuery("""
    SELECT 
        C.ID AS CompanyID,
        C.Name AS CompanyName,
        SUM(CAST(E.income AS DECIMAL)) AS TotalRevenue
    FROM 
        Company C
    LEFT JOIN 
        events E ON C.ID = E.company_id
    GROUP BY 
        C.ID, CompanyName
    ORDER BY 
        TotalRevenue DESC;
""")

    customer_loyalty = runQuery("""
        SELECT 
            C.ID AS CustomerID, 
            CONCAT(C.first_name, ' ', C.last_name) AS CustomerName,
            Co.ID AS CompanyID,
            Co.Name AS CompanyName,
            COUNT(P.purchase_id) AS PurchaseCount
        FROM 
            Purchase P
        JOIN 
            Customer C ON P.customer_id = C.ID
        JOIN 
            TICKET T ON P.ticket_id = T.ID
        JOIN 
            events E ON T.event_id = E.ID
        JOIN 
            Company Co ON E.company_id = Co.ID
        GROUP BY 
            C.ID, CustomerName, Co.ID, CompanyName
        ORDER BY 
            CustomerID, CompanyID;
    """)

    event_type_popularity = runQuery("""
        SELECT 
            E.type AS EventType, 
            COUNT(T.event_id) AS TotalTicketsSold
        FROM 
            events E
        JOIN 
            TICKET T ON E.ID = T.event_id
        GROUP BY 
            E.type
        ORDER BY 
            TotalTicketsSold DESC;
    """)
    events = runQuery("SELECT * FROM events")
    companies = runQuery("SELECT * FROM Company")
    distributers = runQuery("SELECT * FROM Distributer")
    customers = runQuery("SELECT * FROM Customer")
    tickets = runQuery("SELECT * FROM Ticket")
    purchases = runQuery("SELECT * FROM Purchase")
    cust_of = runQuery("SELECT * FROM cust_of")

    return render_template('events.html', events=events, companies=companies, distributers=distributers, customers=customers, tickets=tickets, purchases=purchases, cust_of=cust_of, most_spending_customer=most_spending_customer, top_revenue_events=top_revenue_events, company_most_event_types=company_most_event_types, company_most_customers=company_most_customers, company_sales_ranking=company_sales_ranking, customer_loyalty=customer_loyalty, event_type_popularity=event_type_popularity)

@app.route('/manage_tickets', methods=['GET', 'POST'])
def manage_tickets():
    if request.method == "POST":
        if 'ID' in request.form and 'type' in request.form  and 'tickets_available' in request.form and 'tickets_sold' in request.form and 'price' in request.form and 'event_id' in request.form and 'distributer_id' in request.form:
            try:
                ticket_id = request.form["ID"]
                type = request.form["type"]
                tickets_available = request.form["tickets_available"]
                tickets_sold = request.form["tickets_sold"]
                price = request.form["price"]
                event_id = request.form["event_id"]
                distributer_id = request.form["distributer_id"]


                
                query = f"""
                INSERT INTO TICKET (ID, type, tickets_available,tickets_sold,price,event_id,distributer_id)
                VALUES ({ticket_id}, '{type}','{tickets_available}','{tickets_sold}','{price}','{event_id}','{distributer_id}');
                """
                runQuery(query)
                
                print(f"Ticket added: {ticket_id}, {price},{distributer_id}")
                
            except Exception as e:
                print(f"Error adding ticket: {e}")
        
        elif 'TicketId' in request.form and 'property' in request.form and 'new_value' in request.form:
                try:
                    ticket_id = request.form["TicketId"]
                    property = request.form["property"]
                    new_value = request.form["new_value"]

                    if property in ["ID", "tickets_available", "tickets_sold", "price", "event_id", "distributer_id"]:

                        new_value = new_value.replace(",", "").replace("$", "")
                        new_value = float(new_value)  
                    else:
                        new_value = f"'{new_value}'"

                  
                    ticket_update_query = f"UPDATE TICKET SET {property} = {new_value} WHERE ID = {ticket_id}"
                    runQuery(ticket_update_query)
                    
              
                    if property == "event_id":
                        event_update_query = f"UPDATE events SET ID = {new_value} WHERE ID = {ticket_id}"
                        runQuery(event_update_query)
                    
                    if property == "distributer_id":
                        distributer_update_query = f"UPDATE Distributer SET ID = {new_value} WHERE ID = {ticket_id}"
                        runQuery(distributer_update_query)

                    print(f"Ticket updated: ID = {ticket_id}, {property} = {new_value}")
                except Exception as e:
                    print(f"Error updating Ticket: {e}")
    

        elif 'TicketID' in request.form:
  
            try:
                ticket_id = request.form["TicketID"]
                runQuery(f"DELETE FROM TICKET WHERE ID = {ticket_id}")
                print(f"Ticket deleted: {ticket_id}")
            except Exception as e:
                print(f"Error deleting ticket: {e}")
    most_spending_customer = runQuery("""
        SELECT 
            C.ID AS CustomerID, 
            CONCAT(C.first_name, ' ', C.last_name) AS CustomerName,
            SUM(T.price) * COUNT(P.purchase_id) AS TotalSpent
        FROM 
            Purchase P
        JOIN 
            TICKET T ON P.ticket_id = T.ID
        JOIN 
            Customer C ON P.customer_id = C.ID
        GROUP BY 
            C.ID, CustomerName
        ORDER BY 
            TotalSpent DESC
        LIMIT 1;
    """)
  
    top_revenue_events = runQuery("""
        SELECT
            ID,
            name AS EventName,
            CAST(income AS DECIMAL) AS TotalRevenue
        FROM 
            events
        ORDER BY 
            TotalRevenue DESC;
    """)
    
    company_most_event_types = runQuery("""
        SELECT 
            C.ID AS CompanyID, 
            C.Name AS CompanyName, 
            COUNT(E.type) AS EventTypeCount
        FROM 
            Company C
        JOIN 
            events E ON C.ID = E.company_id
        GROUP BY 
            C.ID, CompanyName
        ORDER BY 
            EventTypeCount DESC
        LIMIT 1;
    """)
    
    company_most_customers = runQuery("""
    SELECT 
        C.ID AS CompanyID,
        C.Name AS CompanyName,
        COUNT(T.event_id) AS TotalTicketsSold
    FROM 
        Company C
    JOIN 
        events E ON C.ID = E.company_id
    JOIN 
        TICKET T ON E.ID = T.event_id
    GROUP BY 
        C.ID, CompanyName
    ORDER BY 
        TotalTicketsSold DESC
    LIMIT 1;
""")
    
    company_sales_ranking = runQuery("""
    SELECT 
        C.ID AS CompanyID,
        C.Name AS CompanyName,
        SUM(CAST(E.income AS DECIMAL)) AS TotalRevenue
    FROM 
        Company C
    LEFT JOIN 
        events E ON C.ID = E.company_id
    GROUP BY 
        C.ID, CompanyName
    ORDER BY 
        TotalRevenue DESC;
""")
    
    customer_loyalty = runQuery("""
        SELECT 
            C.ID AS CustomerID, 
            CONCAT(C.first_name, ' ', C.last_name) AS CustomerName,
            Co.ID AS CompanyID,
            Co.Name AS CompanyName,
            COUNT(P.purchase_id) AS PurchaseCount
        FROM 
            Purchase P
        JOIN 
            Customer C ON P.customer_id = C.ID
        JOIN 
            TICKET T ON P.ticket_id = T.ID
        JOIN 
            events E ON T.event_id = E.ID
        JOIN 
            Company Co ON E.company_id = Co.ID
        GROUP BY 
            C.ID, CustomerName, Co.ID, CompanyName
        ORDER BY 
            CustomerID, CompanyID;
    """)
    
    event_type_popularity = runQuery("""
        SELECT 
            E.type AS EventType, 
            COUNT(T.event_id) AS TotalTicketsSold
        FROM 
            events E
        JOIN 
            TICKET T ON E.ID = T.event_id
        GROUP BY 
            E.type
        ORDER BY 
            TotalTicketsSold DESC;
    """)
    events = runQuery("SELECT * FROM events")
    companies = runQuery("SELECT * FROM Company")
    distributers = runQuery("SELECT * FROM Distributer")
    customers = runQuery("SELECT * FROM Customer")
    tickets = runQuery("SELECT * FROM Ticket")
    purchases = runQuery("SELECT * FROM Purchase")
    cust_of = runQuery("SELECT * FROM cust_of")

    return render_template('events.html', events=events, companies=companies, distributers=distributers, customers=customers, tickets=tickets, purchases=purchases, cust_of=cust_of, most_spending_customer=most_spending_customer, top_revenue_events=top_revenue_events, company_most_event_types=company_most_event_types, company_most_customers=company_most_customers, company_sales_ranking=company_sales_ranking, customer_loyalty=customer_loyalty, event_type_popularity=event_type_popularity)

@app.route('/manage_purchase', methods=['GET', 'POST'])
def manage_purchase():
    if request.method == "POST":
      
        
        
        if 'purchase_id' in request.form and 'customer_id' in request.form and 'ticket_id' in request.form and 'payment_type' in request.form and 'purchase_date' in request.form:
         
            try:
                purchase_id = request.form["purchase_id"]
                customer_id = request.form["customer_id"]
                ticket_id = request.form["ticket_id"]
                payment_type = request.form["payment_type"]
                purchase_date = request.form["purchase_date"]

                query = f"""
                INSERT INTO Purchase (purchase_id, customer_id, ticket_id, payment_type, purchase_date)
                VALUES ({purchase_id}, '{customer_id}', '{ticket_id}', '{payment_type}', '{purchase_date}');
                """
                runQuery(query)
                
                print(f"Purchase added: {purchase_id}, {customer_id}, {ticket_id}")
                
            except Exception as e:
                print(f"Error adding purchase: {e}")

        
        
        elif 'PurchaseID' in request.form:
            try:
                purchase_id = request.form["PurchaseID"]
                print(f"Deleting purchase with ID: {purchase_id}")  

                result = runQuery(f"SELECT ticket_id FROM Purchase WHERE purchase_id = {purchase_id}")
                ticket_id = result[0][0] if result else None

                runQuery(f"DELETE FROM Purchase WHERE purchase_id = {purchase_id}")

                if ticket_id:
                    runQuery(f"DELETE FROM TICKET WHERE ID = {ticket_id}")
                
                print(f"Purchase and related ticket deleted: {purchase_id}, {ticket_id}")
            except Exception as e:
                print(f"Error deleting Purchase: {e}")
    most_spending_customer = runQuery("""
        SELECT 
            C.ID AS CustomerID, 
            CONCAT(C.first_name, ' ', C.last_name) AS CustomerName,
            SUM(T.price) * COUNT(P.purchase_id) AS TotalSpent
        FROM 
            Purchase P
        JOIN 
            TICKET T ON P.ticket_id = T.ID
        JOIN 
            Customer C ON P.customer_id = C.ID
        GROUP BY 
            C.ID, CustomerName
        ORDER BY 
            TotalSpent DESC
        LIMIT 1;
    """)
    

    top_revenue_events = runQuery("""
        SELECT
            ID,
            name AS EventName,
            CAST(income AS DECIMAL) AS TotalRevenue
        FROM 
            events
        ORDER BY 
            TotalRevenue DESC;
    """)
   
    company_most_event_types = runQuery("""
        SELECT 
            C.ID AS CompanyID, 
            C.Name AS CompanyName, 
            COUNT(E.type) AS EventTypeCount
        FROM 
            Company C
        JOIN 
            events E ON C.ID = E.company_id
        GROUP BY 
            C.ID, CompanyName
        ORDER BY 
            EventTypeCount DESC
        LIMIT 1;
    """)
    
    company_most_customers = runQuery("""
    SELECT 
        C.ID AS CompanyID,
        C.Name AS CompanyName,
        COUNT(T.event_id) AS TotalTicketsSold
    FROM 
        Company C
    JOIN 
        events E ON C.ID = E.company_id
    JOIN 
        TICKET T ON E.ID = T.event_id
    GROUP BY 
        C.ID, CompanyName
    ORDER BY 
        TotalTicketsSold DESC
    LIMIT 1;
""")
    
    company_sales_ranking = runQuery("""
    SELECT 
        C.ID AS CompanyID,
        C.Name AS CompanyName,
        SUM(CAST(E.income AS DECIMAL)) AS TotalRevenue
    FROM 
        Company C
    LEFT JOIN 
        events E ON C.ID = E.company_id
    GROUP BY 
        C.ID, CompanyName
    ORDER BY 
        TotalRevenue DESC;
""")
    
    customer_loyalty = runQuery("""
        SELECT 
            C.ID AS CustomerID, 
            CONCAT(C.first_name, ' ', C.last_name) AS CustomerName,
            Co.ID AS CompanyID,
            Co.Name AS CompanyName,
            COUNT(P.purchase_id) AS PurchaseCount
        FROM 
            Purchase P
        JOIN 
            Customer C ON P.customer_id = C.ID
        JOIN 
            TICKET T ON P.ticket_id = T.ID
        JOIN 
            events E ON T.event_id = E.ID
        JOIN 
            Company Co ON E.company_id = Co.ID
        GROUP BY 
            C.ID, CustomerName, Co.ID, CompanyName
        ORDER BY 
            CustomerID, CompanyID;
    """)
    
    event_type_popularity = runQuery("""
        SELECT 
            E.type AS EventType, 
            COUNT(T.event_id) AS TotalTicketsSold
        FROM 
            events E
        JOIN 
            TICKET T ON E.ID = T.event_id
        GROUP BY 
            E.type
        ORDER BY 
            TotalTicketsSold DESC;
    """)
    events = runQuery("SELECT * FROM events")
    companies = runQuery("SELECT * FROM Company")
    distributers = runQuery("SELECT * FROM Distributer")
    customers = runQuery("SELECT * FROM Customer")
    tickets = runQuery("SELECT * FROM TICKET")
    purchases = runQuery("SELECT * FROM Purchase")
    cust_of = runQuery("SELECT * FROM cust_of")

    return render_template('events.html', events=events, companies=companies, distributers=distributers, customers=customers, tickets=tickets, purchases=purchases, cust_of=cust_of, most_spending_customer=most_spending_customer, top_revenue_events=top_revenue_events, company_most_event_types=company_most_event_types, company_most_customers=company_most_customers, company_sales_ranking=company_sales_ranking, customer_loyalty=customer_loyalty, event_type_popularity=event_type_popularity)
@app.route('/manage_cust_of', methods=['GET', 'POST'])
def manage_cust_of():
    if request.method == "POST":
        if 'company_id' in request.form and 'customer_id' in request.form:
            try:
                company_id = request.form["company_id"]
                customer_id = request.form["customer_id"]
                
                runQuery("INSERT INTO cust_of (company_id, customer_id) VALUES (%s, %s)", (company_id, customer_id))
                print(f"cust_of added: {company_id}, {customer_id}")
                
            except Exception as e:
                print(f"Error adding cust_of: {e}")
        
        elif 'cust_ofID' in request.form:
            try:
                cust_of_id = request.form["cust_ofID"]
                print(f"cust_ofID: {cust_of_id}")  
                company_id, customer_id = cust_of_id.split(',')
                print(f"Parsed company_id: {company_id}, customer_id: {customer_id}") 

                print(f"Deleting relationship: company_id = {company_id}, customer_id = {customer_id}")
                runQuery("DELETE FROM cust_of WHERE company_id = %s AND customer_id = %s", (company_id, customer_id))
                runQuery(f"DELETE FROM Customer WHERE ID = {customer_id}")
                print(f"cust_of deleted: {cust_of_id}")
            except Exception as e:
                print(f"Error deleting cust_of: {e}")
    most_spending_customer = runQuery("""
        SELECT 
            C.ID AS CustomerID, 
            CONCAT(C.first_name, ' ', C.last_name) AS CustomerName,
            SUM(T.price) * COUNT(P.purchase_id) AS TotalSpent
        FROM 
            Purchase P
        JOIN 
            TICKET T ON P.ticket_id = T.ID
        JOIN 
            Customer C ON P.customer_id = C.ID
        GROUP BY 
            C.ID, CustomerName
        ORDER BY 
            TotalSpent DESC
        LIMIT 1;
    """)
  
    top_revenue_events = runQuery("""
        SELECT
            ID,
            name AS EventName,
            CAST(income AS DECIMAL) AS TotalRevenue
        FROM 
            events
        ORDER BY 
            TotalRevenue DESC;
    """)
    
    company_most_event_types = runQuery("""
        SELECT 
            C.ID AS CompanyID, 
            C.Name AS CompanyName, 
            COUNT(E.type) AS EventTypeCount
        FROM 
            Company C
        JOIN 
            events E ON C.ID = E.company_id
        GROUP BY 
            C.ID, CompanyName
        ORDER BY 
            EventTypeCount DESC
        LIMIT 1;
    """)
    
    company_most_customers = runQuery("""
    SELECT 
        C.ID AS CompanyID,
        C.Name AS CompanyName,
        COUNT(T.event_id) AS TotalTicketsSold
    FROM 
        Company C
    JOIN 
        events E ON C.ID = E.company_id
    JOIN 
        TICKET T ON E.ID = T.event_id
    GROUP BY 
        C.ID, CompanyName
    ORDER BY 
        TotalTicketsSold DESC
    LIMIT 1;
""")
    
    company_sales_ranking = runQuery("""
    SELECT 
        C.ID AS CompanyID,
        C.Name AS CompanyName,
        SUM(CAST(E.income AS DECIMAL)) AS TotalRevenue
    FROM 
        Company C
    LEFT JOIN 
        events E ON C.ID = E.company_id
    GROUP BY 
        C.ID, CompanyName
    ORDER BY 
        TotalRevenue DESC;
""")
    
    customer_loyalty = runQuery("""
        SELECT 
            C.ID AS CustomerID, 
            CONCAT(C.first_name, ' ', C.last_name) AS CustomerName,
            Co.ID AS CompanyID,
            Co.Name AS CompanyName,
            COUNT(P.purchase_id) AS PurchaseCount
        FROM 
            Purchase P
        JOIN 
            Customer C ON P.customer_id = C.ID
        JOIN 
            TICKET T ON P.ticket_id = T.ID
        JOIN 
            events E ON T.event_id = E.ID
        JOIN 
            Company Co ON E.company_id = Co.ID
        GROUP BY 
            C.ID, CustomerName, Co.ID, CompanyName
        ORDER BY 
            CustomerID, CompanyID;
    """)
    
    event_type_popularity = runQuery("""
        SELECT 
            E.type AS EventType, 
            COUNT(T.event_id) AS TotalTicketsSold
        FROM 
            events E
        JOIN 
            TICKET T ON E.ID = T.event_id
        GROUP BY 
            E.type
        ORDER BY 
            TotalTicketsSold DESC;
    """)
    events = runQuery("SELECT * FROM events")
    companies = runQuery("SELECT * FROM Company")
    distributers = runQuery("SELECT * FROM Distributer")
    customers = runQuery("SELECT * FROM Customer")
    tickets = runQuery("SELECT * FROM Ticket")
    purchases = runQuery("SELECT * FROM Purchase")
    cust_of = runQuery("SELECT company_id, customer_id FROM cust_of")
    return render_template('events.html', events=events, companies=companies, distributers=distributers, customers=customers, tickets=tickets, purchases=purchases, cust_of=cust_of, most_spending_customer=most_spending_customer, top_revenue_events=top_revenue_events, company_most_event_types=company_most_event_types, company_most_customers=company_most_customers, company_sales_ranking=company_sales_ranking, customer_loyalty=customer_loyalty, event_type_popularity=event_type_popularity)

@app.route('/manage_events_manager', methods=['GET', 'POST'])
def manage_events_manager():
    if request.method == "POST":
        if 'ID' in request.form and 'name' in request.form and 'type' in request.form and 'location' in request.form and 'income' in request.form and 'expense' in request.form and 'datetime' in request.form and 'details' in request.form and 'company_id' in request.form and 'general' in request.form and 'vipp' in request.form:
            try:
                event_id = request.form["ID"]
                name = request.form["name"]
                event_type = request.form["type"]
                location = request.form["location"]
                event_datetime = request.form["datetime"]
                general = request.form["general"]
                vip = request.form["vipp"]
                income = request.form["income"]
                expense = request.form["expense"]
                details = request.form["details"]
                company_id = request.form["company_id"]
                
                query = f"""
                INSERT INTO events (ID, name, type, location, datetime, general_price, vip_price, income, expense, details, company_id)
                VALUES ({event_id}, '{name}', '{event_type}', '{location}', '{event_datetime}', '{general}', '{vip}', '{income}', '{expense}', '{details}', {company_id});
                """
                runQuery(query)
                
                print(f"Event added: {event_id}, {name}")
                
            except Exception as e:
                print(f"Error adding event: {e}")
        
        elif 'EventId' in request.form and 'property' in request.form and 'new_value' in request.form:
            try:
                event_id = request.form["EventId"]
                property = request.form["property"]
                new_value = request.form["new_value"]

                if property == "datetime":
                    new_value = f"'{new_value}'"
                elif property in ["general_price", "vip_price", "company_id"]:
         
                    new_value = new_value.replace(",", "").replace("$", "")
                    new_value = float(new_value) 
                else:
                    new_value = f"'{new_value}'"

                query = f"UPDATE events SET {property} = {new_value} WHERE ID = {event_id}"
                runQuery(query)
                
                    
                    
                        
                print(f"Event updated: ID = {event_id}, {property} = {new_value}")
            except Exception as e:
                print(f"Error updating event: {e}")
        
        elif 'EventId' in request.form:
       
            try:
                event_id = request.form["EventId"]
                runQuery(f"DELETE FROM events WHERE ID = {event_id}")
                print(f"Event deleted: {event_id}")
            except Exception as e:
                print(f"Error deleting event: {e}")
    top_revenue_events = runQuery("""
        SELECT 
            name AS EventName,
            CAST(income AS DECIMAL) AS TotalRevenue
        FROM 
            events
        ORDER BY 
            TotalRevenue DESC;
    """)
    
    company_most_event_types = runQuery("""
        SELECT 
            C.ID AS CompanyID, 
            C.Name AS CompanyName, 
            COUNT(E.type) AS EventTypeCount
        FROM 
            Company C
        JOIN 
            events E ON C.ID = E.company_id
        GROUP BY 
            C.ID, CompanyName
        ORDER BY 
            EventTypeCount DESC
        LIMIT 1;
    """)
    
    company_sales_ranking = runQuery("""
    SELECT 
        C.ID AS CompanyID,
        C.Name AS CompanyName,
        SUM(CAST(E.income AS DECIMAL)) AS TotalRevenue
    FROM 
        Company C
    LEFT JOIN 
        events E ON C.ID = E.company_id
    GROUP BY 
        C.ID, CompanyName
    ORDER BY 
        TotalRevenue DESC;
""")
    customer_loyalty = runQuery("""
        SELECT 
            C.ID AS CustomerID, 
            CONCAT(C.first_name, ' ', C.last_name) AS CustomerName,
            Co.ID AS CompanyID,
            Co.Name AS CompanyName,
            COUNT(P.purchase_id) AS PurchaseCount
        FROM 
            Purchase P
        JOIN 
            Customer C ON P.customer_id = C.ID
        JOIN 
            TICKET T ON P.ticket_id = T.ID
        JOIN 
            events E ON T.event_id = E.ID
        JOIN 
            Company Co ON E.company_id = Co.ID
        GROUP BY 
            C.ID, CustomerName, Co.ID, CompanyName
        ORDER BY 
            CustomerID, CompanyID;
    """)
    
    event_type_popularity = runQuery("""
        SELECT 
            E.type AS EventType, 
            COUNT(T.event_id) AS TotalTicketsSold
        FROM 
            events E
        JOIN 
            TICKET T ON E.ID = T.event_id
        GROUP BY 
            E.type
        ORDER BY 
            TotalTicketsSold DESC;
    """)

    events = runQuery("SELECT e.ID,e.name,e.type,e.location,e.datetime,e.general_price,e.vip_price,e.income,e.expense,e.details,c.name AS company_name FROM events e JOIN Company c ON e.company_id = c.ID;")
    companies = runQuery("SELECT * FROM Company")
    distributers = runQuery("SELECT * FROM Distributer")
    customers = runQuery("SELECT * FROM Customer")
    tickets = runQuery("SELECT * FROM Ticket")
    purchases = runQuery("SELECT * FROM Purchase")
    cust_of = runQuery("SELECT * FROM cust_of")

    return render_template('manager.html', events=events, companies=companies, distributers=distributers, customers=customers, tickets=tickets, purchases=purchases, cust_of=cust_of, top_revenue_events=top_revenue_events, company_most_event_types=company_most_event_types, company_sales_ranking=company_sales_ranking, customer_loyalty=customer_loyalty, event_type_popularity=event_type_popularity)

@app.route('/manage_events', methods=['GET', 'POST'])
def manage_events():
    if request.method == "POST":
        if 'ID' in request.form and 'name' in request.form and 'type' in request.form and 'location' in request.form and 'income' in request.form and 'expense' in request.form and 'datetime' in request.form and 'details' in request.form and 'company_id' in request.form and 'general' in request.form and 'vipp' in request.form:
            try:
                event_id = request.form["ID"]
                name = request.form["name"]
                event_type = request.form["type"]
                location = request.form["location"]
                event_datetime = request.form["datetime"]
                general = request.form["general"]
                vip = request.form["vipp"]
                income = request.form["income"]
                expense = request.form["expense"]
                details = request.form["details"]
                company_id = request.form["company_id"]
                
                query = f"""
                INSERT INTO events (ID, name, type, location, datetime, general_price, vip_price, income, expense, details, company_id)
                VALUES ({event_id}, '{name}', '{event_type}', '{location}', '{event_datetime}', '{general}', '{vip}', '{income}', '{expense}', '{details}', {company_id});
                """
                runQuery(query)
                
                print(f"Event added: {event_id}, {name}")
                
            except Exception as e:
                print(f"Error adding event: {e}")
        
        elif 'EventId' in request.form and 'property' in request.form and 'new_value' in request.form:
            try:
                event_id = request.form["EventId"]
                property = request.form["property"]
                new_value = request.form["new_value"]
                if property == "datetime":
                    new_value = f"'{new_value}'"
                elif property in ["general_price", "vip_price", "company_id"]:
                    new_value = new_value.replace(",", "").replace("$", "")
                    new_value = float(new_value)  
                else:
                    new_value = f"'{new_value}'"

                query = f"UPDATE events SET {property} = {new_value} WHERE ID = {event_id}"
                runQuery(query)
                
                    
                    
                        
                print(f"Event updated: ID = {event_id}, {property} = {new_value}")
            except Exception as e:
                print(f"Error updating event: {e}")
        
        elif 'EventId' in request.form:
            try:
                event_id = request.form["EventId"]
                runQuery(f"DELETE FROM events WHERE ID = {event_id}")
                print(f"Event deleted: {event_id}")
            except Exception as e:
                print(f"Error deleting event: {e}")
    most_spending_customer = runQuery("""
        SELECT 
            C.ID AS CustomerID, 
            CONCAT(C.first_name, ' ', C.last_name) AS CustomerName,
            SUM(T.price) * COUNT(P.purchase_id) AS TotalSpent
        FROM 
            Purchase P
        JOIN 
            TICKET T ON P.ticket_id = T.ID
        JOIN 
            Customer C ON P.customer_id = C.ID
        GROUP BY 
            C.ID, CustomerName
        ORDER BY 
            TotalSpent DESC
        LIMIT 1;
    """)
    
    top_revenue_events = runQuery("""
        SELECT
            ID,
            name AS EventName,
            CAST(income AS DECIMAL) AS TotalRevenue
        FROM 
            events
        ORDER BY 
            TotalRevenue DESC;
    """)
    company_most_event_types = runQuery("""
        SELECT 
            C.ID AS CompanyID, 
            C.Name AS CompanyName, 
            COUNT(E.type) AS EventTypeCount
        FROM 
            Company C
        JOIN 
            events E ON C.ID = E.company_id
        GROUP BY 
            C.ID, CompanyName
        ORDER BY 
            EventTypeCount DESC
        LIMIT 1;
    """)
    
    company_most_customers = runQuery("""
    SELECT 
        C.ID AS CompanyID,
        C.Name AS CompanyName,
        COUNT(T.event_id) AS TotalTicketsSold
    FROM 
        Company C
    JOIN 
        events E ON C.ID = E.company_id
    JOIN 
        TICKET T ON E.ID = T.event_id
    GROUP BY 
        C.ID, CompanyName
    ORDER BY 
        TotalTicketsSold DESC
    LIMIT 1;
""")
    
    company_sales_ranking = runQuery("""
    SELECT 
        C.ID AS CompanyID,
        C.Name AS CompanyName,
        SUM(CAST(E.income AS DECIMAL)) AS TotalRevenue
    FROM 
        Company C
    LEFT JOIN 
        events E ON C.ID = E.company_id
    GROUP BY 
        C.ID, CompanyName
    ORDER BY 
        TotalRevenue DESC;
""")
    
    customer_loyalty = runQuery("""
        SELECT 
            C.ID AS CustomerID, 
            CONCAT(C.first_name, ' ', C.last_name) AS CustomerName,
            Co.ID AS CompanyID,
            Co.Name AS CompanyName,
            COUNT(P.purchase_id) AS PurchaseCount
        FROM 
            Purchase P
        JOIN 
            Customer C ON P.customer_id = C.ID
        JOIN 
            TICKET T ON P.ticket_id = T.ID
        JOIN 
            events E ON T.event_id = E.ID
        JOIN 
            Company Co ON E.company_id = Co.ID
        GROUP BY 
            C.ID, CustomerName, Co.ID, CompanyName
        ORDER BY 
            CustomerID, CompanyID;
    """)
    
    event_type_popularity = runQuery("""
        SELECT 
            E.type AS EventType, 
            COUNT(T.event_id) AS TotalTicketsSold
        FROM 
            events E
        JOIN 
            TICKET T ON E.ID = T.event_id
        GROUP BY 
            E.type
        ORDER BY 
            TotalTicketsSold DESC;
    """)
    events = runQuery("SELECT * FROM events")
    companies = runQuery("SELECT * FROM Company")
    distributers = runQuery("SELECT * FROM Distributer")
    customers = runQuery("SELECT * FROM Customer")
    tickets = runQuery("SELECT * FROM Ticket")
    purchases = runQuery("SELECT * FROM Purchase")
    cust_of = runQuery("SELECT * FROM cust_of")

    return render_template('events.html', events=events, companies=companies, distributers=distributers, customers=customers, tickets=tickets, purchases=purchases, cust_of=cust_of, most_spending_customer=most_spending_customer, top_revenue_events=top_revenue_events, company_most_event_types=company_most_event_types, company_most_customers=company_most_customers, company_sales_ranking=company_sales_ranking, customer_loyalty=customer_loyalty, event_type_popularity=event_type_popularity)

if __name__ == '__main__':
    app.run(debug=True)


