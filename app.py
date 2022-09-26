from asyncio.windows_events import NULL
from flask import Flask, render_template, request, jsonify,redirect,url_for
import os, sys,logging,string,random
import pymongo 
from pymongo import MongoClient

connected = 0
user_first_name = ""
usr =  ""
usr_passport =  ""
role = -1
active = 0

app = Flask(__name__)

def get_db():
    client = MongoClient('mongodb://localhost:27017')
    db = client["DSAirlines"]
    return db

@app.route('/',methods=['GET','POST'])
def login():
    return render_template('index.html',msg="")

# Η παρακάτω συνάρτηση δέχεται το username και το password απο την σελίδα σύνδεσης.
# Συνδέεται στη βάση και ελέγχει αν υπάρχει ή όχι ο χρήστης και στην περίπτωση που υπάρχει 
# ελέγχει εάν το password που έχει δώσει είναι το σωστό.

@app.route('/login_handler',methods=['GET','POST'])
def login_handler():

    global connected
    global user_first_name
    global usr
    global usr_passport
    global role
    global active

    # Σύνδεση στη βάση
    db = get_db()

    # Επιλογή του collection users το οποίο περιέχει τους εγγεγραμμένους χρήστες
    collection = db['users']

    # Αναζήτηση του χρήστη με username το username που έδωσε ο χρήστης στη σελίδα σύνδεσης
    res = collection.find({"username": request.form['uname']})

    # Εκχώρηση των επιστρεφόμενων (ιδανικά πρέπει να είναι 1) σε λίστα
    lst=list(res)

    # Αν δεν βρεθεί χρήστης με το συγκεκριμένο username δοκιμάζεται μηπως έχει δοθεί password
    if(len(lst)==0):
        # Αναζήτηση του χρήστη με email το username που έδωσε ο χρήστης στη σελίδα σύνδεσης
        res = collection.find({"email": request.form['uname']})

        # Εκχώρηση των επιστρεφόμενων (ιδανικά πρέπει να είναι 1) σε λίστα
        lst=list(res)
        
        # Αν δεν βρεθεί χρήστης με το συγκεκριμένο email επιστροφή στη σελίδα σύνδεσης 
        # και εμφάνιση σχετικού μηνύματος σφάλματος
        if(len(lst)==0):
            return render_template('index.html',msg="Invalid username or email!")
        else:
        # Εάν η εκτέλεση φτάσει εδώ, σημαίνει ότι ο χρήστης υπάρχει 
        # Eπαναλαμβάνουμε την αναζήτηση με email   
            res = collection.find({"email": request.form['uname']})
    else:
    # Εάν η εκτέλεση φτάσει εδώ, σημαίνει ότι ο χρήστης υπάρχει
    # Eπαναλαμβάνουμε την αναζήτηση με username 
        res = collection.find({"username": request.form['uname']})
    
    # Μένει να δούμε εάν έχει δώσει και το σωστό password
    # Επαναλαμβάνεται η ερώτηση στη βάση (η μετατροπή σε λίστα δημιουργεί πρόβλημα στον cursor)
    
    # Eντοπίζεται ο πρώτος (και μοναδικός) επιστρεφόμενος χρήστης
    user = res.next()

    # Εντοπίζεται το ορθό password
    correct_pass=user["password"]

    # Περίπτωση στην οποία ο χρήστης πιστοποιήθηκε
    if(request.form['pass']==correct_pass):
        
        # Εντοπίζεται αν ο χρήστης είναι ενεργός
        active=user["active"]

        # Αν δεν είναι επιστρέφει στην αρχική σελίδα σύνδεσης
        if(active==0):
            return render_template('index.html',msg="User is not active!")

        # Διαφορετικά εντοπίζεται ο ρόλος του (απλός χρήστης ή διαχειριστής)
        role=user["role"]

        # O χρήστης θεωρείται πλεον συνδεδεμένος
        connected=1

        # Κρατείται το username του
        usr=user['username']

        # Κρατείται το passport του
        usr_passport=user["passport"]

        msg="Welcome "+usr+"!"

        # Σύμφωνα με τον ρόλο του γίνεται ανακατεύθυνση στο αντίστοιχο μενού
        if(role==0):
           return render_template('user_menu.html',msg=msg)     
        elif(role==1):
            return render_template('admin_menu.html',msg=msg) 
        else:
            return render_template('change_pass.html',msg=msg) 

    # Στην περίπτωση στην οποία ο χρήστης δεν πιστοποιήθηκε ανακατεύθυνση στη σελίδα σύνδεσης
    else:        
        return render_template('index.html',msg="Invalid password!")


# Η παρακάτω συνάρτηση διαχειρίζεται την αναζήτηση πτήσης αφού ο χρήστης έχει συνδεθεί
@app.route('/search_flight',methods=['GET','POST'])
def search_flight():

    global connected
    global user_first_name
    global usr
    global usr_passport
    global role
    global active

    # Eαν δεν έχει γίνει σύνδεση ανακατεύθυνση στην αρχική
    if(connected<=0):
        return render_template('index.html')

    return render_template('user_menu.html')

@app.route('/flight_search_handler',methods=['GET','POST'])
def flight_search():

    # Eαν δεν έχει γίνει σύνδεση ανακατεύθυνση στην αρχική
    if(connected<=0):
        return render_template('index.html')

    # Σύνδεση στη βάση
    db = get_db()

    # Επιλογή του collection users το οποίο περιέχει τις πτήσεις
    collection = db['flights']

    # Αναζήτηση των πτήσεων με τη δεδομένη ημερομηνία και την δεδομένη πόλη αναχώρησης και 
    # πόλη προορισμού
    res = collection.find({"date": request.form['flight_date'],"departure": request.form['departure'],"destination": request.form['destination']})

    # Εκχώρηση των επιστρεφόμενων σε λίστα
    lst=list(res)

    # Υπολογισμος πληθους πτησεων που βρεθηκαν
    num_of_found_flights=len(lst)
        
    res = collection.find({"date": request.form['flight_date'],"departure": request.form['departure'],"destination": request.form['destination']})

    return render_template('found_flights.html',fl=res,n=num_of_found_flights)

# Προσθήκη κράτησης
@app.route('/new_reservation')
def new_reservation():
 
    global connected
    global user_first_name
    global usr
    global usr_passport
    global role
    global active

    # Eαν δεν έχει γίνει σύνδεση ανακατεύθυνση στην αρχική
    if(connected<=0):
        return render_template('index.html')

    return render_template('new_reservation.html',u_con=connected,u_active=active)

@app.route('/new_reservation_handler',methods=['GET','POST'])
def new_reservation_handler():

    global connected
    global user_first_name
    global usr
    global usr_passport
    global role
    global active

    # Eαν δεν έχει γίνει σύνδεση ανακατεύθυνση στην αρχική
    if(connected<=0):
        return render_template('index.html')

    # Σύνδεση στη βάση
    db = get_db()

    # Επιλογή του collection flights το οποίο περιέχει τις πτήσεις
    collection = db['flights']

    # Αναζήτηση των πτήσεων με τον δεδομένο κωδικό
    res = collection.find({"code": request.form['fcode']})

    # Εκχώρηση των επιστρεφόμενων σε λίστα
    lst=list(res)

    # Υπολογισμος πληθους πτησεων που βρεθηκαν
    num_of_found_flights=len(lst)

    # Aν δεν βρέθηκε ακριβως μία πτήση επιστροφή στην αναζήτηση
    if(num_of_found_flights!=1):
        return render_template('new_reservation.html',u_con=connected,u_active=active,msg="Flight code not exists!")

    # Aν βρέθηκε ακριβως μία πτήση ελέγχεται εάν ο αριθμός της κάρτας έχει 16 χαρακτήρες 
    if(len(request.form['cardnum'])!=16):
        return render_template('new_reservation.html',u_con=connected,u_active=active,msg="Card number must have 16 characters!")
    
    # Aν η κάρτα έχει 16 χαρακτήρες ελέγχεται αν όλοι οι χαρακτήρες είναι ψηφία του δεκαδικού
    if(request.form['cardnum'].isdecimal()==False):
        return render_template('new_reservation.html',u_con=connected,u_active=active,msg="Card number can only contain decimal digits!")
  
    # Διαφορετικά ελέγχεται το πλήθος των διαθέσιμων θέσεων    
    res = collection.find({"code": request.form['fcode']})
    
    # Υπολογισμος πληθους πτησεων που βρεθηκαν
    num_of_found_flights=len(lst)
        
    res = collection.find({'code': request.form['fcode']})

    for flight in res:
        num_of_available_seats=flight["available_seats"]
    
    # Εάν δεν υπάρχουν θέσεις, εμφανίζεται μήνυμα σφάλματος και δεν γίνεται κράτηση
    if(num_of_available_seats==0):
        return render_template('new_reservation.html',u_con=connected,u_active=active,msg="Flight is full!")
    
    # Μείωση των ελεύθερων θέσεων κατά μία
    collection.update_one({'code': request.form['fcode']}, {'$set': {'available_seats': num_of_available_seats-1 }})
    
    # Προσθήκη κράτησης

    # Επιλογή του collection reservations το οποίο περιέχει τις κρατήσεις
    collection = db['reservations']
    
    # Υπολογισμός του νέου id (κατα 1 μεγαλύτερο από το μέχρι τώρα μέγιστο)
    new_id=collection.find_one(sort=[("id",-1)])['id']+1

    # Κατασκευή νέας κράτησης
    new_reservation = { 'id': new_id, 'passenger': usr, 'passport': usr_passport, 'flight': request.form['fcode'] }

    # Εισαγωγή νέας κρατησης
    collection.insert_one(new_reservation)

    # Επιστροφή
    return render_template('user_menu.html',msg="New reservation:Success! Reservation id: "+str(new_id)) 

# Εμφάνιση κράτησης
@app.route('/view_reservation')
def view_reservation():

    global connected
    global user_first_name
    global usr
    global usr_passport
    global role
    global active

    # Eαν δεν έχει γίνει σύνδεση ανακατεύθυνση στην αρχική
    if(connected<=0):
        return render_template('index.html')

    return render_template('view_reservation.html',u_con=connected,u_active=active)

@app.route('/view_reservation_handler',methods=['GET','POST'])
def view_reservation_handler():

    global connected
    global user_first_name
    global usr
    global usr_passport
    global role
    global active

    # Eαν δεν έχει γίνει σύνδεση ανακατεύθυνση στην αρχική
    if(connected<=0):
        return render_template('index.html')

    # Eλέγχεται αν ο κωδικός κράτησης είναι ακέραιος
    if(request.form['resid'].isdecimal()==False):
        return render_template('view_reservation.html',u_con=connected,u_active=active,msg="Reservation id can only contains decimal digits!")
   
    # Σύνδεση στη βάση
    db = get_db()

    # Επιλογή του collection reservations το οποίο περιέχει τις κρατήσεις
    collection = db['reservations']

    # Αναζήτηση των κρατήσεων με τον δεδομένο κωδικό
    res = collection.find({'id': int(request.form['resid'])})

    # Εκχώρηση των επιστρεφόμενων σε λίστα
    lst=list(res)

    # Υπολογισμος πληθους κρατήσεων που βρεθηκαν (ιδανικά πρέπει να είναι μία)
    num_of_found_reservations=len(lst)

    # Aν δεν βρέθηκε ακριβως μία κράτηση επιστροφή στην αναζήτηση
    if(num_of_found_reservations!=1):
        return render_template('view_reservation.html',u_con=connected,u_active=active,msg="Reservation id not exists!")

    # Aν βρέθηκε ακριβως μία κράτηση τότε η κράτηση ανασύρεται ξανα 
    found_reservation = collection.find_one({'id': int(request.form['resid'])})

    # Σε περίπτωση που η κράτηση έχει γίνει από άλλον χρήστη, δεν υπάρχει δικαίωμα προσπέλασης
    if(found_reservation['passenger']!=usr):
        return render_template('view_reservation.html',u_con=connected,u_active=active,msg="This reservation have been done from another customer!")
    
    # Κατασκευή επιστρεφόμενης κράτησης 
    return_reservation = "Id: "+str(found_reservation['id'])+" | "
    return_reservation = return_reservation +"Passenger: "+str(found_reservation['passenger'])+" | "
    return_reservation = return_reservation +"Passport: "+str(found_reservation['passport'])+" | "
    return_reservation = return_reservation +"Flight: "+str(found_reservation['flight'])

    # Επιστροφή κράτησης
    return render_template('view_reservation.html',u_con=connected,u_active=active,msg=return_reservation)
 

# Ακύρωση κράτησης
@app.route('/cancel_reservation')
def cancel_reservation():
    return render_template('cancel_reservation.html',u_con=connected,u_active=active)

@app.route('/cancel_reservation_handler',methods=['GET','POST'])
def cancel_reservation_handler():

    global connected
    global user_first_name
    global usr
    global usr_passport
    global role
    global active

    # Eαν δεν έχει γίνει σύνδεση ανακατεύθυνση στην αρχική
    if(connected<=0):
        return render_template('index.html')

    # Σύνδεση στη βάση
    db = get_db()

    # Επιλογή του collection reservations το οποίο περιέχει τις κρατήσεις
    collection = db['reservations']

    # Eλέγχεται αν ο κωδικός κράτησης είναι ακέραιος
    if(request.form['resid'].isdecimal()==False):
        return render_template('view_reservation.html',u_con=connected,u_active=active,msg="Reservation id can only contains decimal digits!")

    # Αναζήτηση των κρατήσεων με τον δεδομένο κωδικό
    res = collection.find({'id': int(request.form['resid'])})

    # Εκχώρηση των επιστρεφόμενων σε λίστα
    lst=list(res)

    # Υπολογισμος πληθους κρατήσεων που βρεθηκαν (ιδανικά πρέπει να είναι μία)
    num_of_found_reservations=len(lst)

    # Aν δεν βρέθηκε ακριβως μία κράτηση επιστροφή στην αναζήτηση
    if(num_of_found_reservations!=1):
        return render_template('cancel_reservation.html',u_con=connected,u_active=active,msg="Reservation id not exists!")
    
    # Aν βρέθηκε ακριβως μία κράτηση τότε η κράτηση ανασύρεται ξανα 
    found_reservation = collection.find_one({'id': int(request.form['resid'])})

    # Σε περίπτωση που η κράτηση έχει γίνει από άλλον χρήστη, δεν υπάρχει δικαίωμα διαγραφής
    if(found_reservation['passenger']!=usr):
        return render_template('cancel_reservation.html',u_con=connected,u_active=active,msg="This reservation have been done from another customer!")

    # Aν βρέθηκε ακριβως μία κράτηση τότε αυτή θα ακυρωθεί 

    # Προτού ακυρωθεί θα πρέπει να κρατηθει η πτήση
    flight_id = found_reservation['flight']
    
    # Aμέσως μετά ακυρώνεται η κράτηση
    collection.delete_one({'id': int(request.form['resid'])})

    # Αφού ακυρωθεί η κράτηση θα πρέπει να αυξηθούν οι διαθέσιμες θέσεις στην αντίστοιχη πτήση
    collection = db['flights']

    # Yπολογίζονται οι διαθέσιμες θέσεις της πτήσης
    res = collection.find({'code': flight_id})
    
    for flight in res:
        num_of_available_seats=flight["available_seats"]
    
    # Αύξηση των ελεύθερων θέσεων κατά μία
    collection.update_one({'code': flight_id}, {'$set': {'available_seats': num_of_available_seats+1 }})
    
    # Επιστροφή
    return render_template('cancel_reservation.html',u_con=connected,u_active=active,msg="Reservation remove: Success!")
    
# Ταξινομημένη εμφάνιση κράτησεων
@app.route('/sorted_reservation_list')
def sorted_reservation_list():

    global connected
    global user_first_name
    global usr
    global usr_passport
    global role
    global active

    # Eαν δεν έχει γίνει σύνδεση ανακατεύθυνση στην αρχική
    if(connected<=0):
        return render_template('index.html')
        
    return render_template('sorted_reservation_list.html',u_con=connected,u_active=active)

@app.route('/sorted_reservation_list_handler',methods=['GET','POST'])
def sorted_reservation_list_handler():

    global connected
    global user_first_name
    global usr
    global usr_passport
    global role
    global active

    # Eαν δεν έχει γίνει σύνδεση ανακατεύθυνση στην αρχική
    if(connected<=0):
        return render_template('index.html')

    # Σύνδεση στη βάση
    db = get_db()

    # Επιλογή του collection reservations το οποίο περιέχει τις κρατήσεις
    collection = db['reservations']
        
    # Αναζήτηση των κρατήσεων του δεδομένου χρήστη
    res = collection.find({'passenger': usr})
        
    # Εκχώρηση των επιστρεφόμενων σε λίστα
    lst=list(res)
    
    # Υπολογισμος πληθους κρατήσεων που βρεθηκαν (ιδανικά πρέπει να είναι μία)
    num_of_found_reservations=len(lst) 

    if(num_of_found_reservations==0):
        return render_template('sorted_reservation_list.html',u_con=connected,u_active=active,msg="No reservation of connected user!")

    if(request.form['time_order']=="older_first"):
        order=-1
    else:
        order=+1

    res=collection.find({'passenger':usr}).sort("id",order)
    
    return render_template('found_reservations.html',rs=res,n=num_of_found_reservations)


# Εμφάνιση ακριβότερης ή φτηνότερης κράτησης
@app.route('/view_cheapest_expensivest_reservation')
def view_cheapest_expensivest_reservation():

    global connected
    global user_first_name
    global usr
    global usr_passport
    global role
    global active

    # Eαν δεν έχει γίνει σύνδεση ανακατεύθυνση στην αρχική
    if(connected<=0):
        return render_template('index.html')

    return render_template('view_cheapest_expensivest_reservation.html',u_con=connected,u_active=active)

@app.route('/view_cheapest_expensivest_reservation_handler',methods=['GET','POST'])
def view_cheapest_expensivest_reservation_handler():

    global connected
    global user_first_name
    global usr
    global usr_passport
    global role
    global active

    # Eαν δεν έχει γίνει σύνδεση ανακατεύθυνση στην αρχική
    if(connected<=0):
        return render_template('index.html')

    # Σύνδεση στη βάση
    db = get_db()

    # Επιλογή του collection reservations το οποίο περιέχει τις κρατήσεις
    collection = db['reservations']

    # Αναζήτηση των κρατήσεων με του συγκεκριμένου χρήστη με χρονολογική σειρά
    # (για την επιλογή της παλαιότερης σε περίπτωση ισότητας κόστους εισιτηρίου)
    res = collection.find({'passenger': usr})
    
    # Εκχώρηση των επιστρεφόμενων σε λίστα
    lst=[]
    for rs in res:
        lst.append(rs['flight'])
   
    # Υπολογισμος πληθους κρατήσεων που βρεθηκαν (ιδανικά πρέπει να είναι μία)
    num_of_found_reservations=len(lst)

    # Aν δεν βρέθηκε ακριβως μία κράτηση επιστροφή στην αναζήτηση
    if(num_of_found_reservations==0):
        return render_template('view_cheapest_expensivest_reservation.html',u_con=connected,u_active=active,msg="No reservations yet!")
    
    # Aαίρεση διπλότυπων από τη λίστα
    lst = list(dict.fromkeys(lst))


    # Βοηθητική σημαία
    flag=0

    # Επιλογή του collection flights το οποίο περιέχει τις πτήσεις
    collection = db['flights']

    st=" "
    # Υπολογίζεται η ακριβότερη και η φτηνότερη κρατηση
    for fcode in lst:
        fl=collection.find_one({'code':fcode})   
        if(fl!=None):   
            if(flag==0):
                min=fl['price']
                code_of_min=fcode
                max=fl['price']
                code_of_max=fcode
                flag=1
            else:
                if(fl['price']<min):
                    min=fl['price']
                    code_of_min=fcode
                if(fl['price']>max):
                    max=fl['price']
                    code_of_max=fcode


    # Επιλογή του collection reservations το οποίο περιέχει τις κρατήσεις
    collection = db['reservations']

    # Αναζήτηση των κρατήσεων με του συγκεκριμένου χρήστη με χρονολογική σειρά
    # (για την επιλογή της παλαιότερης σε περίπτωση ισότητας κόστους εισιτηρίου)
    res = collection.find({'passenger': usr}).sort('id', +1)

    if(request.form['price_order']=="cheapest"):
        found_reservation=collection.find_one({'flight':code_of_min},sort=[('id',+1)])
    else:
        found_reservation=collection.find_one({'flight':code_of_max},sort=[('id',+1)])

    # Κατασκευή επιστρεφόμενης κράτησης 
    return_reservation = "Id: "+str(found_reservation['id'])+" | "
    return_reservation = return_reservation +"Passenger: "+str(found_reservation['passenger'])+" | "
    return_reservation = return_reservation +"Passport: "+str(found_reservation['passport'])+" | "
    return_reservation = return_reservation +"Flight: "+str(found_reservation['flight'])+" | "

    if(request.form['price_order']=="cheapest"):
        return_reservation = return_reservation +"Price: "+str(min)
    else:
        return_reservation = return_reservation +"Price: "+str(max)

    # Επιστροφή κράτησης
    return render_template('view_cheapest_expensivest_reservation.html',u_con=connected,u_active=active,msg=return_reservation)
 

# Εμφάνιση κρατήσεων συγκεκριμένου προορισμού
@app.route('/view_reservations_of_certain_destination')
def view_reservations_of_certain_destination():

    global connected
    global user_first_name
    global usr
    global usr_passport
    global role
    global active

    # Eαν δεν έχει γίνει σύνδεση ανακατεύθυνση στην αρχική
    if(connected<=0):
        return render_template('index.html')

    return render_template('view_reservations_of_certain_destination.html',u_con=connected,u_active=active)

@app.route('/view_reservations_of_certain_destination_handler',methods=['GET','POST'])
def view_reservations_of_certain_destination_handler():

    global connected
    global user_first_name
    global usr
    global usr_passport
    global role
    global active

    # Eαν δεν έχει γίνει σύνδεση ανακατεύθυνση στην αρχική
    if(connected<=0):
        return render_template('index.html')

    # Σύνδεση στη βάση
    db = get_db()

    # Επιλογή του collection flights το οποίο περιέχει τις πτήσεις
    collection = db['flights']

    # Αναζήτηση των κωδικών πτήσεων με το συγκεκριμένο προορισμό
    res = collection.find({'destination': request.form['destination']})

    # Εκχώρηση των επιστρεφόμενων σε λίστα
    flight_codes=[]

    for rs in res:
        flight_codes.append(rs['code'])

    # Υπολογισμος πληθους κρατήσεων που βρεθηκαν
    num_of_found_reservations=len(flight_codes)

    if(num_of_found_reservations==0):
         return render_template('view_reservations_of_certain_destination.html',u_con=connected,u_active=active,msg="No reservations for the selected destination!")
    
    # Επιλογή του collection reservations το οποίο περιέχει τις κρατήσεις
    collection = db['reservations']

    # Αναζήτηση των κρατήσεων με του συγκεκριμένου χρήστη 
    res = collection.find({'passenger': usr})

    # Αρχικοποίηση λίστας επιστροφής
    return_reservations = []

    # Κατασκευή λίστας επιστροφής
    num_of_found_reservations=0
    for rsv in res:
        if(rsv['flight'] in flight_codes):
            return_reservation = "Id: "+str(rsv['id'])+" | "
            return_reservation = return_reservation +"Passenger: "+str(rsv['passenger'])+" | "
            return_reservation = return_reservation +"Passport: "+str(rsv['passport'])+" | "
            return_reservation = return_reservation +"Flight: "+str(rsv['flight'])+" | "
            return_reservation = return_reservation +"Destination: "+request.form['destination']
            return_reservations.append(return_reservation)
            num_of_found_reservations=num_of_found_reservations+1
    # Επιστροφή κρατήσεων
    return render_template('found_reservations_of_destinations.html',rs=return_reservations,n=num_of_found_reservations)
 

@app.route('/deactivate_account')
def deactivate_account():

    global connected
    global user_first_name
    global usr
    global usr_passport
    global role
    global active

    # Eαν δεν έχει γίνει σύνδεση ανακατεύθυνση στην αρχική
    if(connected<=0):
        return render_template('index.html')

    # Eντοπίζεται ο κωδικός ανάκτησης
    db = get_db()
    collection = db['users']

    recovery = collection.find_one({'username': usr})['recovery']

    # Αποστέλλεται ο κωδικός ανάκτησης στη σελίδα επιβεβαίωσης
    return render_template('deactivate_account.html',msg="Copy your reactivate code: "+str(recovery))

@app.route('/deactivate_account_handler',methods=['GET','POST'])
def deactivate_account_handler():

    global connected
    global user_first_name
    global usr
    global usr_passport
    global role
    global active

      # Eαν δεν έχει γίνει σύνδεση ανακατεύθυνση στην αρχική
    if(connected<=0):
        return render_template('index.html')

    # Eντοπίζεται ο κωδικός ανάκτησης
    db = get_db()
    collection = db['users']

    collection.update_one({'username': usr}, {'$set': {'active':0 }})

    # Μηδενίζονται οι global μεταβλητές active και connected
    active=0
    connected=0
    
    # Ανακατεύθυνση στη σελίδα σύνδεσης
    return render_template('index.html')


@app.route('/flights')
def get_stored_flights():
    db = get_db()
    collection = db['flights']
    res = collection.find()

    flights = [ { "date": flight["date"],"time": flight["time"],"departure": flight["departure"],"destination": flight["destination"],"price": flight["price"],"hours": flight["hours"],"available_seats": flight["available_seats"]} for flight in res  ]

    return flights

# Ανάκτηση λογαριασμού
@app.route('/reactivation')
def reactivation():

    return render_template('reactivate.html')


@app.route('/reactivation_handler',methods=['GET','POST'])
def reactivation_handler():

    # Εντοπίζεται η ύπαρξη του χρήστη
    db = get_db()
    collection = db['users']

    res = collection.find({'username': request.form['uname']})

    count=0
    for found_user in res:
        count=count+1

    # Αν δεν υπάρχει ο χρήστης επιστρέφεται σφάλμα
    if(count==0):
        return render_template('reactivate.html',msg="Reactivation failed. Invaid username.")

    # Αν ο κωδικός ανάκτησης δεν είναι σωστός επιστρέφεται σφάλμα
    if(request.form['recovery']!=found_user['recovery']):
        return render_template('reactivate.html',msg="Reactivation failed. Invaid reactivation code.")
    
    # Διαφορετικά γίνεται ανάκτηση
    collection.update_one({'username': request.form['uname']}, {'$set': {'active': 1 }})

    return render_template('index.html',msg="Reactivation: Success!")


# Εγγραφή
@app.route('/signup')
def signup():

    return render_template('signup.html')


@app.route('/signup_handler',methods=['GET','POST'])
def signup_handler():

    # Σε πρώτη φάση ελέγχουμε εαν το username υπάρχει
    db = get_db()
    collection = db['users']

    res = collection.find({'username': request.form['uname']})

    count=0
    for found_user in res:
        count=count+1
    
    # Σε περίπτωση που υπάρχει χρήστης με το εν λόγω Username επιστρέφεται μηνυμα σφάλματος 
    # και γίνεται ανακατεύθυνση στη σελίδα εγγραφής.
    if(count>0):
        return render_template('signup.html',msg="Username already exists!")

    # Σε δεύτερη φάση ελέγχουμε εαν το email υπάρχει
    res = collection.find({'email': request.form['email']})

    count=0
    for found_user in res:
        count=count+1
    
    # Σε περίπτωση που υπάρχει χρήστης με το εν λόγω email επιστρέφεται μηνυμα σφάλματος 
    # και γίνεται ανακατεύθυνση στη σελίδα εγγραφής.
    if(count>0):
        return render_template('signup.html',msg="Email already exists!")

    # Eλέγχεται αν το  password εχει μήκος τουλάχιστον 8
    # Σε περίπτωση που δεν συμβαίνει κάτι τέτοιο επιστρέφεται μηνυμα σφάλματος 
    # και γίνεται ανακατεύθυνση στη σελίδα εγγραφής.
    if(len(request.form['pass'])<8):
        return render_template('signup.html',msg="Password must contain at least 8 characters!")
    
    # Eλέγχεται αν το  password περιέχει τουλάχιστον ένα νούμερο
    # Σε περίπτωση που δεν συμβαίνει κάτι τέτοιο επιστρέφεται μηνυμα σφάλματος 
    # και γίνεται ανακατεύθυνση στη σελίδα εγγραφής.
    if(any(char.isdigit() for char in request.form['pass'])==False):
        return render_template('signup.html',msg="Password must contain at least one digit!")
    
    # Eλέγχεται αν τα δύο  password ταιριάζουν
    # Σε περίπτωση που δεν συμβαίνει κάτι τέτοιο επιστρέφεται μηνυμα σφάλματος 
    # και γίνεται ανακατεύθυνση στη σελίδα εγγραφής.
    if(request.form['pass']!=request.form['cpass']):
        return render_template('signup.html',msg="Password mismatch!")

    # Eλέγχεται αν τo passport αποτελείται από 9 χαρακτήρες
    # Σε περίπτωση που δεν συμβαίνει κάτι τέτοιο επιστρέφεται μηνυμα σφάλματος 
    # και γίνεται ανακατεύθυνση στη σελίδα εγγραφής.
    if(len(request.form['passport'])!=9):
        return render_template('signup.html',msg="Passport must consist of 9 characters")
   
    # Eλέγχεται αν οι πρώτοι δύο χαρακτήρες είναι γράμματα
    # Σε περίπτωση που δεν συμβαίνει κάτι τέτοιο επιστρέφεται μηνυμα σφάλματος 
    # και γίνεται ανακατεύθυνση στη σελίδα εγγραφής.
    count=0
    if(request.form['passport'][0].isalpha()):
        count=count+1
    if(request.form['passport'][1].isalpha()):
        count=count+1

    if(count!=2):
        return render_template('signup.html',msg="First 2 passport characters must be letters")
    
    # Eλέγχεται αν οι υπόλοιποι χαρακτήρες είναι αριθμοί
    # Σε περίπτωση που δεν συμβαίνει κάτι τέτοιο επιστρέφεται μηνυμα σφάλματος 
    # και γίνεται ανακατεύθυνση στη σελίδα εγγραφής.   
    count=0
    for i in range(2, 9):
        if(request.form['passport'][i].isdigit()):
            count=count+1

    if(count!=7):
        return render_template('signup.html',msg="Last 7 passport characters must be digits")

    # Δημιουργία τυχαίο κωδικού recovery 12 χαρακτήρων
    letters = string.ascii_lowercase
    recovery = ''.join(random.choice(letters) for i in range(12))

    # Εισαγωγή νέου χρήστη
    new_user= { 'email': request.form['email'], 'username': request.form['uname'], 'password': request.form['pass'], 'name': request.form['name'], 'surname': request.form['surname'],'passport': request.form['passport'],'active': 1, 'role': 0, 'recovery': recovery} 

    collection.insert_one(new_user)

    # Επιστροφή στην αρχική
    return render_template('index.html')


@app.route('/admin_menu',methods=['GET','POST'])
def admin_menu():

    global connected
    global user_first_name
    global usr
    global usr_passport
    global role
    global active

    # Eαν δεν έχει γίνει σύνδεση ανακατεύθυνση στην αρχική
    if(connected<=0):
        return render_template('index.html')

    # Eάν ο ρόλος δεν είναι διαχειριστή ανακατεύθυνση στην αρχική
    if(role<1):
        return render_template('index.html')

    return render_template('admin_menu.html')


@app.route('/flight_add_handler',methods=['GET','POST'])
def flight_add_handler():

    global connected
    global user_first_name
    global usr
    global usr_passport
    global role
    global active

    # Eαν δεν έχει γίνει σύνδεση ανακατεύθυνση στην αρχική
    if(connected<=0):
        return render_template('index.html')

    # Eάν ο ρόλος δεν είναι διαχειριστή ανακατεύθυνση στην αρχική
    if(role<1):
        return render_template('index.html')

    # Διαβάζεται δοσμένη η ημερομηνία νέας πτήσης
    date=request.form['flight_date']
    
    # Διαβάζεται η ώρα νέας πτήσης
    time=request.form['hour']+":"+request.form['minute']

    # Διαβάζεται η πόλη αναχώρησησης
    departure=request.form['departure']

    # Διαβάζεται η πόλη προορισμού
    destination=request.form['destination']

    # Αν είναι ίδιες επιστρέφεται μήνυμα σφάλματος
    if(departure==destination):
        return render_template('admin_menu.html',msg="Destination must be different than departure")

    # Διαβάζεται η διάρκεια του ταξιδιού
    hours=request.form['hours']     

    # Διαβάζεται η τιμή του ταξιδιού
    price_str=request.form['price']     

    # Θα πρέπει να είναι θετικός αριθμός
    try:
        price = float(price_str)
    except ValueError:
        return render_template('admin_menu.html',msg="Price must be a positive number")

    if(price<=0):
        return render_template('admin_menu.html',msg="Price must be a positive number")

    # Κατασκευή κωδικού
    code=departure[0]+destination[0]+date[2]+date[3]+date[5]+date[6]+date[8]+date[9]+request.form['hour']
    
    # Εισαγωγή νέας πτήσης
    new_flight = { 'code': code, 'date': date, 'time': time, 'departure': departure, 'destination': destination,'price': price,'hours': hours, 'available_seats': 220} 

    db = get_db()
    collection = db['flights']

    collection.insert_one(new_flight)

    return render_template('admin_menu.html',msg="Add new flight: Success!")

# Εγγραφή
@app.route('/add_admin')
def add_admin():

    return render_template('add_admin.html')


@app.route('/add_admin_handler',methods=['GET','POST'])
def add_admin_handler():

    global connected
    global user_first_name
    global usr
    global usr_passport
    global role
    global active

    # Eαν δεν έχει γίνει σύνδεση ανακατεύθυνση στην αρχική
    if(connected<=0):
        return render_template('index.html')

    # Eάν ο ρόλος δεν είναι διαχειριστή ανακατεύθυνση στην αρχική
    if(role<1):
        return render_template('index.html')

    # Σε πρώτη φάση ελέγχουμε εαν το username υπάρχει
    db = get_db()
    collection = db['users']

    res = collection.find({'username': request.form['uname']})

    count=0
    for found_user in res:
        count=count+1
    
    # Σε περίπτωση που υπάρχει χρήστης με το εν λόγω Username επιστρέφεται μηνυμα σφάλματος 
    # και γίνεται ανακατεύθυνση στη σελίδα εγγραφής.
    if(count>0):
        return render_template('signup.html',msg="Username already exists!")

    # Σε δεύτερη φάση ελέγχουμε εαν το email υπάρχει

    res = collection.find({'email': request.form['email']})

    count=0
    for found_user in res:
        count=count+1
    
    # Σε περίπτωση που υπάρχει χρήστης με το εν λόγω email επιστρέφεται μηνυμα σφάλματος 
    # και γίνεται ανακατεύθυνση στη σελίδα εγγραφής.
    if(count>0):
        return render_template('signup.html',msg="Email already exists!")

    # Eλέγχεται αν το  password εχει μήκος τουλάχιστον 8
    # Σε περίπτωση που δεν συμβαίνει κάτι τέτοιο επιστρέφεται μηνυμα σφάλματος 
    # και γίνεται ανακατεύθυνση στη σελίδα εγγραφής.
    if(len(request.form['pass'])<8):
        return render_template('signup.html',msg="Password must contain at least 8 characters!")
    
    # Eλέγχεται αν το  password περιέχει τουλάχιστον ένα νούμερο
    # Σε περίπτωση που δεν συμβαίνει κάτι τέτοιο επιστρέφεται μηνυμα σφάλματος 
    # και γίνεται ανακατεύθυνση στη σελίδα εγγραφής.
    if(any(char.isdigit() for char in request.form['pass'])==False):
        return render_template('signup.html',msg="Password must contain at least one digit!")
    
    # Eλέγχεται αν τα δύο  password ταιριάζουν
    # Σε περίπτωση που δεν συμβαίνει κάτι τέτοιο επιστρέφεται μηνυμα σφάλματος 
    # και γίνεται ανακατεύθυνση στη σελίδα εγγραφής.
    if(request.form['pass']!=request.form['cpass']):
        return render_template('signup.html',msg="Password mismatch!")

    # Eλέγχεται αν τo passport αποτελείται από 9 χαρακτήρες
    # Σε περίπτωση που δεν συμβαίνει κάτι τέτοιο επιστρέφεται μηνυμα σφάλματος 
    # και γίνεται ανακατεύθυνση στη σελίδα εγγραφής.
    if(len(request.form['passport'])!=9):
        return render_template('signup.html',msg="Passport must consist of 9 characters")
   
    # Eλέγχεται αν οι πρώτοι δύο χαρακτήρες είναι γράμματα
    # Σε περίπτωση που δεν συμβαίνει κάτι τέτοιο επιστρέφεται μηνυμα σφάλματος 
    # και γίνεται ανακατεύθυνση στη σελίδα εγγραφής.
    count=0
    if(request.form['passport'][0].isalpha()):
        count=count+1
    if(request.form['passport'][1].isalpha()):
        count=count+1

    if(count!=2):
        return render_template('signup.html',msg="First 2 passport characters must be letters")
    
    # Eλέγχεται αν οι υπόλοιποι χαρακτήρες είναι αριθμοί
    # Σε περίπτωση που δεν συμβαίνει κάτι τέτοιο επιστρέφεται μηνυμα σφάλματος 
    # και γίνεται ανακατεύθυνση στη σελίδα εγγραφής.   
    count=0
    for i in range(2, 9):
        if(request.form['passport'][i].isdigit()):
            count=count+1

    if(count!=7):
        return render_template('signup.html',msg="Last 7 passport characters must be digits")

    # Δημιουργία τυχαίο κωδικού recovery 12 χαρακτήρων
    letters = string.ascii_lowercase
    recovery = ''.join(random.choice(letters) for i in range(12))

    # Εισαγωγή νέου χρήστη
    new_user= { 'email': request.form['email'], 'username': request.form['uname'], 'password': request.form['pass'], 'name': request.form['name'], 'surname': request.form['surname'],'passport': request.form['passport'],'active': 1, 'role': 2, 'recovery': recovery} 

    collection.insert_one(new_user)

    # Επιστροφή στην αρχική
    return render_template('index.html')


# Εγγραφή
@app.route('/change_pass')
def change_pass():

    return render_template('change_pass.html')


@app.route('/change_pass_handler',methods=['GET','POST'])
def change_pass_handler():

    global connected
    global user_first_name
    global usr
    global usr_passport
    global role
    global active

    # Eαν δεν έχει γίνει σύνδεση ανακατεύθυνση στην αρχική
    if(connected<=0):
        return render_template('index.html')

    # Eάν ο ρόλος δεν είναι διαχειριστή ανακατεύθυνση στην αρχική
    if(role<1):
        return render_template('index.html')

    # Eλέγχεται αν το  password εχει μήκος τουλάχιστον 8
    # Σε περίπτωση που δεν συμβαίνει κάτι τέτοιο επιστρέφεται μηνυμα σφάλματος 
    # και γίνεται ανακατεύθυνση στη σελίδα  αλλαγης password.
    if(len(request.form['pass'])<8):
        return render_template('change_pass.html',msg="Password must contain at least 8 characters!")
    
    # Eλέγχεται αν το  password περιέχει τουλάχιστον ένα νούμερο
    # Σε περίπτωση που δεν συμβαίνει κάτι τέτοιο επιστρέφεται μηνυμα σφάλματος 
    # και γίνεται ανακατεύθυνση στη σελίδα αλλαγης password.
    if(any(char.isdigit() for char in request.form['pass'])==False):
        return render_template('change_pass.html',msg="Password must contain at least one digit!")
    
    # Eλέγχεται αν τα δύο  password ταιριάζουν
    # Σε περίπτωση που δεν συμβαίνει κάτι τέτοιο επιστρέφεται μηνυμα σφάλματος 
    # και γίνεται ανακατεύθυνση στη σελίδα  αλλαγης password.
    if(request.form['pass']!=request.form['cpass']):
        return render_template('change_pass.html',msg="Password mismatch!")

    db = get_db()
    collection = db['users']

    # Ενημερωση password 
    collection.update_one({'username': usr}, {'$set': {'passport': request.form['pass'] }})
   
    # Ενημερωση rρόλου (απο 2 γινεται 1 έτσι ώστε να μην απαιτείται πλεον αλλαγή password) 
    collection.update_one({'username': usr}, {'$set': {'role':1 }})
    
    # Eνημερώνεται και η global μεταβλητή που ορίζει τον ρόλο
    role = 1

    # Eντοπιζεται ο κωδικός επαναφοράς
    recovery=collection.find_one({'username': usr})['recovery']

    msg = "New admin password change: Success! Recovery code: "+recovery

    # Ανακατεύθυνση στο μενου του admin
    return render_template('admin_menu.html',msg=msg) 

# Η παρακάτω συνάρτηση διαχειρίζεται την αλλαγή τιμής μιας πτήσης από τον εναν admin
@app.route('/admin_change_price',methods=['GET','POST'])
def admin_change_price():

    global connected
    global user_first_name
    global usr
    global usr_passport
    global role
    global active

    # Eαν δεν έχει γίνει σύνδεση ανακατεύθυνση στην αρχική
    if(connected<=0):
        return render_template('index.html')

    # Eαν ο χρήστης δεν είναι admin σύνδεση ανακατεύθυνση στην αρχική
    if(role!=1):
        return render_template('index.html')

    return render_template('admin_change_price.html')

@app.route('/admin_change_price_handler',methods=['GET','POST'])
def admin_change_price_handler():

    global connected
    global user_first_name
    global usr
    global usr_passport
    global role
    global active

    # Eαν δεν έχει γίνει σύνδεση ανακατεύθυνση στην αρχική
    if(connected<=0):
        return render_template('index.html')

    # Eαν ο χρήστης δεν είναι admin σύνδεση ανακατεύθυνση στην αρχική
    if(role!=1):
        return render_template('index.html')

    # Σύνδεση στη βάση
    db = get_db()

    # Επιλογή του collection flights το οποίο περιέχει τις πτήσεις
    collection = db['flights']

    # Αναζήτηση της πτήσης με τον κωδικό που έχει δοθεί στην φόρμα
    res = collection.find({"code": request.form['fcode']})

    # Εκχώρηση των επιστρεφόμενων πτήσεων σε λίστα (ιδανικά πρέπει να είναι μία)
    lst=list(res)

    # Υπολογισμος πληθους πτησεων που βρεθηκαν
    num_of_found_flights=len(lst)

    # Αν δεν βρέθηκε πτήση επιστρέφεται σφάλμα
    if(num_of_found_flights==0):
        return render_template('admin_change_price.html',msg="Flight not found!")

    # Αν βρέθηκαν πολλές πτήσεις πάλι επιστρέφεται σφάλμα
    if(num_of_found_flights>1):
        return render_template('admin_change_price.html',msg="More than onw flights found!")

    # Αν η εκτέλεση φτάσει εδώ σημαίνει ότι ορθώς βρέθηκε ακριβώς μία πτήση

    # Διαβάζεται η μοναδική πτήση για την οποία θέλουμε να αλάξουμε τιμή
    fl=collection.find_one({'code':request.form['fcode']})

    # Διαβάζεται η τιμή του ταξιδιού
    price_str=request.form['new_price']     

    # Θα πρέπει να είναι θετικός αριθμός
    try:
        price = float(price_str)
    except ValueError:
        return render_template('admin_change_price.html',msg="Price must be a positive number")

    # Αν η πτήση δεν είναι άδεια, δεν μπορεί να αλλάξει η τιμή
    if(price<=0):
        return render_template('admin_change_price.html',msg="Price must be a positive number")

    # Aν η πτήση είναι γεμάτη δεν μπορεί να γίνει αλλαγή τιμής
    if(fl['available_seats']!=220):
        return render_template('admin_change_price.html',msg="Flight has already reservations. Can not change price!")

    collection.update_one({'code': request.form['fcode']}, {'$set': {'price': float(request.form['new_price']) }})
   
    # Επιτυχής επιστροφή
    return render_template('admin_change_price.html',msg="Price change: Success!")

# Ακύρωση πτήσης
@app.route('/admin_cancel_flight',methods=['GET','POST'])
def admin_cancel_flight():

    global connected
    global user_first_name
    global usr
    global usr_passport
    global role
    global active

    # Eαν δεν έχει γίνει σύνδεση ανακατεύθυνση στην αρχική
    if(connected<=0):
        return render_template('index.html')

    # Eαν ο χρήστης δεν είναι admin σύνδεση ανακατεύθυνση στην αρχική
    if(role!=1):
        return render_template('index.html')

    return render_template('admin_cancel_flight.html')

# Η παρακάτω συνάρτηση διαχειρίζεται την ακύρωση μιας πτήσης από τον εναν admin
@app.route('/admin_cancel_flight_handler',methods=['GET','POST'])
def admin_cancel_flight_handler():

    global connected
    global user_first_name
    global usr
    global usr_passport
    global role
    global active

    # Eαν δεν έχει γίνει σύνδεση ανακατεύθυνση στην αρχική
    if(connected<=0):
        return render_template('index.html')

    # Eαν ο χρήστης δεν είναι admin σύνδεση ανακατεύθυνση στην αρχική
    if(role!=1):
        return render_template('index.html')

    # Σύνδεση στη βάση
    db = get_db()

    # Επιλογή του collection flights το οποίο περιέχει τις πτήσεις
    collection = db['flights']

    # Αναζήτηση της πτήσης με τον κωδικό που έχει δοθεί στην φόρμα
    res = collection.find({"code": request.form['fcode']})

    # Εκχώρηση των επιστρεφόμενων σε λίστα
    lst=list(res)

    # Υπολογισμος πληθους πτησεων που βρεθηκαν
    num_of_found_flights=len(lst)

    # Αν δεν βρέθηκε πτήση επιστρέφεται σφάλμα
    if(num_of_found_flights==0):
        return render_template('admin_cancel_flight.html',msg="Flight not found!")

    # Αν βρέθηκαν πολλές πτήσεις πάλι επιστρέφεται σφάλμα
    if(num_of_found_flights>1):
        return render_template('admin_cancel_flight.html',msg="More than onw flights found!")
       
    # Αν η εκτέλεση φτάσει εδώ σημαίνει ότι ορθώς βρέθηκε ακριβώς μία πτήση

    # Διαγραφή πτήσης
    collection.delete_one({'code':request.form['fcode']})

    # Επιτυχής επιστροφή
    return render_template('admin_change_price.html',msg="Flight deletion: Success!")

if __name__=='__main__':
    app.run(host="0.0.0.0", port=5000,debug=True)