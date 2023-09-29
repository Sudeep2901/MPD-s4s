from __future__ import unicode_literals

from werkzeug.wrappers import Response

import frappe.sessions
import frappe.utils
from frappe import _, is_whitelisted

from frappe import get_all
import requests
import frappe
import ast
import re
from twilio.rest import Client 
import math, random
from datetime import datetime
from frappe import auth
from frappe.client import get_list,set_value
from frappe import _
from frappe.utils import date_diff, flt, getdate
import json
from datetime import date
# import locale
from urllib.error import HTTPError
from erpnext.stock.doctype.purchase_receipt.purchase_receipt import make_purchase_invoice
from erpnext.stock.doctype.purchase_receipt.purchase_receipt import make_stock_entry

@frappe.whitelist()
def hide_fields(s_user):
    user_doc = frappe.get_doc("User",{"name":s_user})
    b = 0
    for i in user_doc.roles:
        if i.role == "S4S CRM Editor":
            b=1
    return b

@frappe.whitelist( allow_guest=True )
def user_login(usr, pwd):
    try:
        login_manager = frappe.auth.LoginManager()
        login_manager.authenticate(user=usr, pwd=pwd)
        login_manager.post_login()
    except frappe.exceptions.AuthenticationError:
        frappe.clear_messages()
        frappe.local.response["message"] = {
            "success_key":0,
            "message":"Authentication Error!"
        }

        return

    api_generate = generate_keys(frappe.session.user)
    user = frappe.get_doc('User', frappe.session.user)
    
                
    frappe.response["message"] = {
        "success_key":1,
        "message":"Authentication success",
        "sid":frappe.session.sid,
        "api_key":user.api_key,
        "api_secret":api_generate,
        "username":user.username,
        "email":user.email,
        "mobile_no":user.mobile_no
    }

def generate_keys(user):
    user_details = frappe.get_doc('User', user)
    api_secret = frappe.generate_hash(length=15)

    if not user_details.api_key:
        api_key = frappe.generate_hash(length=15)
        user_details.api_key = api_key

    user_details.api_secret = api_secret
    user_details.save()
    # print(api_secret)

    return api_secret

@frappe.whitelist()
def item_price(item_code):
    success = 0
    msg = "Failed"
    item_price = 0.00
    if frappe.db.exists("Item",item_code):
        success = 1
        if frappe.db.exists("Item Price",{"item_code":item_code}):
            doc = frappe.get_last_doc("Item Price",{"item_code":item_code,"buying":1})
            item_price = doc.price_list_rate
            msg = "Found"
        else:
            item_price = 0.00
            msg = "Not Found"
    
    frappe.response["success"] = success
    frappe.response["message"] = msg
    frappe.response["item_price"] = item_price
        
@frappe.whitelist(allow_guest=True,methods=["GET","POST","PUT"])
def mob_no_verification(mobile_no):
    success = 0
    msg = "Failed"
    OTP = ""
    msg_sid = ""
    ts = ""
    # if re.fullmatch('[6-9][0-9]{9}',mobileNumber)!=None:
    if frappe.db.exists("User",{"mobile_no":mobile_no,"enabled":1})!=None or frappe.db.exists("User",{"mobile_no":"+91"+mobile_no,"enabled":1})!=None:
        user = frappe.get_value("User",{"mobile_no":mobile_no}) if frappe.db.exists("User",{"mobile_no":mobile_no})!=None else frappe.get_value("User",{"mobile_no":"+91"+mobile_no})
        print(user)
        # if role in frappe.get_roles(user):
        print(all(x in frappe.get_roles(user) for x in ["VLCC User","CC User"]))
        if any(x in frappe.get_roles(user) for x in ["VLCC User","CC User"]):
            twilio_settings = frappe.get_doc("S4S Twilio Settings")
            if twilio_settings.enabled == 1:
                digits = "0123456789"
                for i in range(4) :
                    OTP += digits[math.floor(random.random() * 10)]

                OTP = "1111"
                    
                dt = datetime.now()
                ts = datetime.timestamp(dt)
                # frappe.db.set_value("OTP Users Data",{"parent":"S4S OTP Verification","user":user,"mobile_number":mob_no or "+91"+mob_no},"timestamp",ts)
                # frappe.db.set_value("OTP Users Data",{"parent":"S4S OTP Verification","user":user,"mobile_number":mob_no or "+91"+mob_no},"otp",OTP)
                # a = set_value(doctype = "OTP Users Data", name = frappe.db.get_value("OTP Users Data",{"parent":"S4S OTP Verification","user":user,"mobile_number":mob_no or "+91"+mob_no},"name"), fieldname = "timestamp", value=ts)
                # b = set_value(doctype = "OTP Users Data", name = frappe.db.get_value("OTP Users Data",{"parent":"S4S OTP Verification","user":user,"mobile_number":mob_no or "+91"+mob_no},"name"), fieldname = "otp", value=OTP)
                frappe.db.sql("""update `tabOTP Users Data` as otp set otp.timestamp = '{0}',otp.otp = '{1}' where otp.parent = 'S4S OTP Verification' and otp.user = '{2}' and otp.mobile_number = '{3}' or  otp.mobile_number = '{4}'""".format(ts,OTP,user,mobile_no,"+91"+mobile_no))
                frappe.db.commit()
                # print()
                #******************* with twilio api
                # account_sid = twilio_settings.account_sid
                # auth_token = twilio_settings.get_password("auth_token")
                # client = Client(account_sid, auth_token)
                # message = client.messages.create(messaging_service_sid=twilio_settings.messaging_service_sid,body=str(OTP)+' is the OTP for your Moomba account. Do not share this OTP with anyone else.',to="+91"+mobileNumber) 
                # if message.sid:
                #**************************END****************
                #******************************with 2factor api
                # url = "https://2factor.in/API/V1/8b79f7d4-df85-11ed-addf-0200cd936042/SMS/+919999999999/12345/OTP1"
                #+++++++++++++++++++
                # pattern = r'^\+91\s\d{10}$'
                # match = re.match(pattern, mobile_no)
                # c_mobile_no = mobile_no if match else "+91 " + mobile_no[-10:]
                # url = "{0}/{1}/SMS/{2}/{3}/OTP1".format(twilio_settings.url,twilio_settings.api_key_2f,c_mobile_no,OTP)
                # payload={}
                # headers = {}
                # response = requests.request("GET", url, headers=headers, data=payload)
                # print(response.text)
                #+++++++++++++++++++#

                success = 1
                msg = "OTP sent successfuly"
                    # msg_sid = message.sid
# 				else:
# 					# success = 500
# 					msg = "Internal Server Error"
# 			else:
# 				# success = 403
# 				msg = "Forbidden"
            
        else:
            # success = 403
            msg = "User Does not have any role VLCC,CC,ME"
    else:
        # success = 404
        msg = "User does not exists with this Mobile Number."
            
    # else:
    # 	# success = 400
    # 	msg = "Bad Request"
    print(msg)
    frappe.response["success"] = success
    frappe.response["message"] = msg
    frappe.response["token"] = ts
    


@frappe.whitelist(allow_guest=True,methods=["GET","POST","PUT"])
def otp_verification(mobile_no,token,otp):
    mob_no=mobile_no
    timestamp=token
    success = 0
    msg = "Failed"
    sid = ""
    api_key = ""
    api_secret = ""
    cc = ""
    vlcc = ""
    full_name = ""
    user_name = ""
    user_role = ""
    company = ""
    if frappe.db.exists("OTP Users Data",{"parent":"S4S OTP Verification","mobile_number":mob_no or "+91"+mob_no}):
        print("True")
        if frappe.db.get_value("OTP Users Data",{"parent":"S4S OTP Verification","mobile_number":mob_no or "+91"+mob_no},"timestamp")==timestamp and frappe.db.get_value("OTP Users Data",{"parent":"S4S OTP Verification","mobile_number":mob_no or "+91"+mob_no},"otp")==otp:
            
            try:
                login_manager = frappe.auth.LoginManager()
                print(login_manager)
                login_manager.authenticate(user="shrikant.pawar@mannlowe.com", pwd="shrikant@123")
                # print(lo)
                login_manager.post_login()
            except frappe.exceptions.AuthenticationError:
                frappe.clear_messages()
                frappe.local.response["message"] = {
                    "success_key":0,
                    "message":"Authentication Error!"
                }

                return
            user = frappe.db.get_value("OTP Users Data",{"parent":"S4S OTP Verification","mobile_number":mob_no or "+91"+mob_no},"user")
            api_generate = generate_keys(user)
            
            user_doc = frappe.get_doc('User', user)
            user_name = user_doc.name
            full_name = user_doc.full_name
            sid = frappe.session.sid
            api_key = user_doc.api_key
            api_secret = api_generate
            # company = user_doc.company
            
            if "CC User" in frappe.get_roles(user):
                user_role += "1"
            if "VLCC User" in frappe.get_roles(user):
                user_role += ",2" if user_role else "2"
            if "ME Field Executive" in frappe.get_roles(user):
                user_role += ",3" if user_role else "3"
            if "Logistic Supervisor" in frappe.get_roles(user):
                user_role += ",4" if user_role else "4"
            success = 1
            msg = "OTP Verified Successfully"
            if frappe.db.exists("S4S User details",user)!=None:
                cc = frappe.get_value("S4S User details",user,"cc_name")
                vlcc = frappe.get_value("S4S User details",user,"vlcc_name")
        else:
            msg = "The OTP entered is incorrect."
    frappe.session.user = None
    frappe.session.sid = None
    if "home_page" in frappe.response:
        del frappe.response["home_page"]
    frappe.response["success"] = success
    frappe.response["message"] = msg
    frappe.response["full_name"] = full_name
    frappe.response["api_key"] = api_key
    frappe.response["secret_key"] = api_secret
    frappe.response["user_email"] = user_name
    frappe.response["user_role"] = user_role
    # frappe.response["company"]=company

@frappe.whitelist(methods=["GET","POST","PUT"])
def get_document_list(doctype,fields=None,filters=None,order_by=None,page_no=1):
    fields = fields if fields is not None else ["name"]
    filters = filters if filters is not None else {"name":["!=",""]}
    order_by = order_by if order_by is not None else "name"
    if doctype:
        count = frappe.db.count(doctype,filters)
        if count!=0:
            total_pages = math.ceil(count/10)
            print(count,total_pages)
            if doctype == "S4S Farmer Query":
                result = get_list(doctype,fields,filters,order_by)
                result = [result[i:i+10] for i in range(0, len(result), 10)]
                if doctype == "S4S Farmer Query" and fields!=['*']:
                    frappe.response["totalCount"] = count
                    frappe.response["items"] = result[int(page_no)-1]
                else:
                    return result
            
@frappe.whitelist(methods=["GET","POST","PUT"])
def get_dashboard_data(user_email,date_from=date.today().strftime("%Y-%m-%d"),date_to=date.today().strftime("%Y-%m-%d")):
    # print(frappe.session)
    success = 0
    msg = "Failed"
    from_date, to_date = date_from, date_to
    last_transaction = {}
    filters={"from_date":from_date,"to_date":to_date,"userEmail":user_email}
    if from_date and from_date!="" and from_date!="null":
        if from_date and not to_date:
            frappe.throw(_("To Date are required."))
        elif date_diff(to_date, from_date) < 0:
            frappe.throw(_("To Date cannot be before From Date."))
    elif to_date and to_date!="" and to_date!="null":
        if not from_date and to_date:
            frappe.throw(_("From Date are required."))
        elif date_diff(to_date, from_date) < 0:
            frappe.throw(_("To Date cannot be before From Date."))
    if user_email and user_email!="" and user_email!="null":
        conditions = ""
        if from_date and to_date:
            conditions += " and sp.transaction_date between %(from_date)s and %(to_date)s"
        data = frappe.db.sql("""
            SELECT
                SUM(sp.total_weight) as total_collection,
                SUM(sp.total_amount)*0.5/100 as total_commission,
                SUM(sp.total_amount) as total_cost,
                (SELECT u.full_name as user_name FROM `tabUser` u WHERE u.name like %(userEmail)s) AS user_name,
                (SELECT udv.vlcc_name as vlcc_name FROM `tabS4S User details` udv WHERE udv.name like %(userEmail)s) as vlcc_name,
                (SELECT udc.cc_name as vlcc_name FROM `tabS4S User details` udc WHERE udc.name like %(userEmail)s) as cc_name
            FROM
                `tabS4S Purchase` sp
            WHERE
                sp.docstatus=1 
                and sp.owner = %(userEmail)s
                {0}
        """.format(
                conditions
            ),
            filters,
            as_dict=1
        )
        transaction = frappe.get_list('S4S Purchase', filters={'owner': user_email}, order_by='creation DESC', limit=1)
        if transaction:
            transaction_doc = frappe.get_doc('S4S Purchase', transaction[0].name)
            last_transaction = {
                "transaction_id": transaction_doc.name,
                "farmer_id": transaction_doc.supplier,
                "farmer_name":transaction_doc.supplier_name,
                "vlcc_name": transaction_doc.vlcc_name,
                "cc_name": transaction_doc.cc_name,
                "date": transaction_doc.transaction_date,
                "product_name": transaction_doc.purchase_receipt_details[0].item_code if transaction_doc.purchase_receipt_details[0] else ""
            }
        success = 1
        msg = "Found"
    
    frappe.response["success"] = success
    frappe.response["message"] = msg
    frappe.response["total_collection"]=float("{:.2f}".format(round(data[0].total_collection,2))) if data[0].total_collection !=None else 0.00
    frappe.response["total_commission"]=float("{:.2f}".format(round(data[0].total_commission,2))) if data[0].total_commission!=None else 0.00
    frappe.response["total_cost"]=float("{:.2f}".format(round(data[0].total_cost,2))) if data[0].total_cost!=None else 0.00
    # frappe.response["total_collection"]=(frappe.utils.fmt_money(data[0].total_collection if data[0].total_collection !=None else 0.00,precision=2,currency="₹")).replace("₹","")
    # frappe.response["total_commission"]=frappe.utils.fmt_money(data[0].total_commission if data[0].total_commission!=None else 0.00,precision=2,currency="₹")
    # frappe.response["total_cost"]=frappe.utils.fmt_money(data[0].total_cost if data[0].total_cost!=None else 0.00,precision=2,currency="₹")
    frappe.response["user_name"]=data[0].user_name
    frappe.response["vlcc_name"]=data[0].vlcc_name
    frappe.response["cc_name"]=data[0].cc_name
    frappe.response["last_transaction"]=last_transaction


    
@frappe.whitelist(methods=["GET","POST","PUT"])
def get_transaction_list(user_id,filters=None,supplier_id=None,from_date=None,to_date=None,page_no=1):
    success,msg,data,totalCount=0,"Failed",[],0
    conditions = ""
    farmerId = supplier_id
    userId = user_id
    pageNo = page_no
    values = {"userId":user_id}
    role = ""

    if frappe.db.exists("User Permission",{"user":userId,"allow":"S4S CC List"}):
        get_usp = frappe.get_all("User Permission",{"user":userId,"allow":"S4S CC List"},["for_value"])
        get_usp = [d['for_value'] for d in get_usp]
        get_usp = "(" + ", ".join(["'" + x + "'" for x in get_usp]) + ")"
        role+= 'sp.cc_name IN {0}'.format(get_usp)
    if frappe.db.exists("User Permission",{"user":userId,"allow":"S4S VLCC List"}):
        get_uspv = frappe.get_all("User Permission",{"user":userId,"allow":"S4S VLCC List"},["for_value"])
        get_uspv = [d['for_value'] for d in get_uspv]
        get_uspv = "(" + ", ".join(["'" + x + "'" for x in get_uspv]) + ")"
        role+= 'sp.vlcc_name IN {0}'.format(get_uspv) if role=="" else ' or sp.vlcc_name IN {0}'.format(get_uspv)
    role = "("+role+")"
    
    if filters!=None and filters!="" and filters!="null":
        values["filters"] = "%%%s%%"%filters
        conditions += "(sp.supplier_name like %(filters)s or sp.vlcc_name like %(filters)s or sp.cc_name like %(filters)s or sp.approved_status like %(filters)s)"
    if farmerId!=None and farmerId!="" and farmerId!="null":
        values["farmerId"] = "%%%s%%"%farmerId
        conditions += "or sp.supplier like %(farmerId)s" if conditions!="" else "sp.supplier like %(farmerId)s"
    if (from_date!=None and from_date!="" and from_date!="null") and (to_date!=None and to_date!=""and to_date!="null"):
        values["from_date"]=from_date
        values["to_date"]=to_date
        conditions += " and sp.transaction_date between %(from_date)s and %(to_date)s" if conditions!="" else " sp.transaction_date between %(from_date)s and %(to_date)s"
    if role!="" and role!=None and role!="null":
        conditions += " AND "+role if conditions!="" else role
    # print(conditions,values)
    all = frappe.db.sql("""
        SELECT
            sp.owner as owner,
            sp.name as transaction_id,
            sp.supplier as supplier_id,
            sp.supplier_name as farmer_name,
            sp.vlcc_name as vlcc_name,
            sp.cc_name as cc_name,
            sp.transaction_date as date,
            sp.total_amount as grand_total,
            sp.total_weight as total_weight,
            sp.weight_after_kadta as weight_after_kadta
        FROM 
            `tabS4S Purchase` sp
            {0}
        ORDER BY
            sp.creation DESC
        """.format(
            "WHERE "+conditions if conditions!="" else conditions 
        ),
        values,
        as_dict=1
    )
    result = []
    for i in all:
        # if i.owner == userId:
        result.append(i)
        if frappe.get_doc("S4S Purchase",i["transaction_id"]).purchase_receipt_details:
            i["product_name"]=frappe.get_doc("S4S Purchase",i["transaction_id"]).purchase_receipt_details[0].item_code
            i["rate"]=frappe.get_doc("S4S Purchase",i["transaction_id"]).purchase_receipt_details[0].rate
        else:
            i["rate"]=""
    count = len(result)
    
    if not count:
        success = 1
        msg = "No Records Found"
    if count !=0:
        total_pages = math.ceil(int(count)/10)
        pageNo = int(pageNo) if int(pageNo)<= total_pages else total_pages
        result = [result[i:i+10] for i in range(0, len(result), 10)]
        success = 1
        msg = "Records Found"
        data = result[int(pageNo)-1]
        for i in data:
            i.pop("owner")
        totalCount = count

    frappe.response["success"] = success
    frappe.response["message"] = msg
    frappe.response["data"] = data
    frappe.response["total_count"] = totalCount

@frappe.whitelist(methods=["GET","POST","PUT"])
def update_inquiry_details(inquiry_id,status):
    success=0
    msg="Failed"
    print(inquiry_id,status,frappe.request)
    if frappe.db.exists("S4S Farmer Query",inquiry_id):
        doc = frappe.get_doc("S4S Farmer Query",inquiry_id)
        if status in ["Active","Inactive","Completed","Pending"]:
            doc.status=status
            doc.meta.bypass_doctype_permission = True
            doc.save()
            success=1
            msg="Inquiry details status updated successfully"
        else:
            success=1
            msg='Status not in "Active","Inactive","Completed","Pending"'
    else:
        success=1
        msg="Inquiry id is not exists"
    frappe.response["success"] = success
    frappe.response["message"] = msg

@frappe.whitelist(methods=["GET","POST","PUT"])
def get_inquiry_list(user_id,status=None,filters=None,farmer_id=None,from_date=None,to_date=None,page_no=1):
    success,msg,data,totalCount=0,"Failed",[],0
    userId=user_id
    farmerId = farmer_id
    pageNo=page_no
    conditions = ""
    values = {"userId":userId}
    if filters!=None and filters!="" and filters!="null":
        values["filters"] = "%%%s%%"%filters
        conditions += "fq.name like %(filters)s or fq.supplier_name like %(filters)s or fq.item_code like %(filters)s or fq.mobile_no like %(filters)s"
    if farmerId!=None and farmerId!="" and farmerId!="null":
        values["farmerId"] = "%%%s%%"%farmerId
        conditions += "or fq.supplier like %(farmerId)s" if conditions!="" else "fq.supplier like %(farmerId)s"
    if (from_date!=None and from_date!="" and from_date!="null") and (to_date!=None and to_date!="" and to_date!="null"):
        values["from_date"]=from_date
        values["to_date"]=to_date
        # print(from_date,to_date)
        conditions += " and (fq.date between %(from_date)s and %(to_date)s)" if conditions!="" else " (fq.date between %(from_date)s and %(to_date)s)"
    

    if status!=None and status!="" and status!="null":
        values["status"]="%s"%status
        conditions+="and fq.status = %(status)s" if conditions!="" else " fq.status = %(status)s"
        # conditions+="and fq.status = '{status}'" if conditions!="" else " fq.status = '{status}'"
    print(conditions)
    print(values)
    all = frappe.db.sql("""
        SELECT
            fq.owner as owner,
            fq.status as status,
            fq.name as inquiry_id,
            fq.supplier_name as farmer_name,
            fq.item_code as product_name,
            fq.supplier as farmer_id,
            fq.date as date,
            fq.rate as rate,
            IF(fq.sample_given = 'Yes', 1, 0) AS sample_given
        FROM 
            `tabS4S Farmer Query` fq
            {0}
        ORDER BY
            fq.creation DESC
        """.format(
            "WHERE "+conditions if conditions!="" else conditions 
        ),
        values,
        as_dict=1
    )
    # print(all)
    result = []
    for i in all:
        if i.owner == userId:
            result.append(i)
    count = len(result)
    if not count:
        success = 1
        msg = "No Records Found"
    if count !=0:
        total_pages = math.ceil(int(count)/10)
        pageNo = int(pageNo) if int(pageNo)<= total_pages else total_pages
        result = [result[i:i+10] for i in range(0, len(result), 10)]
        success = 1
        msg = "Records Found"
        data = result[int(pageNo)-1]
        for i in data:
            i.pop("owner")
        totalCount = count

    frappe.response["success"] = success
    frappe.response["message"] = msg
    frappe.response["data"] = data
    frappe.response["total_count"] = totalCount

@frappe.whitelist(methods=["GET","POST","PUT"])
def get_farmer_details(farmer_id):
    farmerId = farmer_id
    success= 0
    msg = "Record Not Found"
    id = ""
    name=""
    supplier_id = "",
    kycDone = ""
    mobNumber=""
    gender= ""
    taluka=""
    state= ""
    district=""
    village=""
    cc_name = ""
    vlcc_name = ""
    if frappe.db.exists("S4S Supplier",{"name":["like","%"+farmerId+"%"],"type_of_supplier":"Farmer"}):
        doc = frappe.get_doc("S4S Supplier",{"name":["like","%"+farmerId+"%"],"type_of_supplier":"Farmer"})
        success= 1
        msg = "Record Found"
        id = doc.name
        name=doc.supplier_name
        supplier_id = doc.supplier
        if doc.supplier:
            kycDone = 1
        elif not doc.supplier and doc.account_holder_name and doc.account_number and doc.bank_name and doc.ifsc_code and doc.branch:	
            kycDone = 2 
        else:
            kycDone = 0
        mobNumber=doc.mobile_no
        gender= doc.gender
        taluka=doc.taluka
        state= doc.state
        district=doc.district
        village=doc.village
        cc_name = doc.cc_name
        vlcc_name = doc.vlcc_name
    frappe.response["success"] = success
    frappe.response["message"] = msg
    frappe.response["id"] = id
    frappe.response["name"] = name
    frappe.response["supplier_id"] = supplier_id
    frappe.response["kyc_status"] = kycDone
    frappe.response["mobile_no"] = mobNumber
    frappe.response["gender"] = gender
    frappe.response["taluka"] = taluka
    frappe.response["state"] = state
    frappe.response["district"] = district
    frappe.response["village"] = village
    frappe.response["cc_name"] = cc_name
    frappe.response["vlcc_name"] = vlcc_name

@frappe.whitelist(methods=["GET","POST","PUT"])
def get_user_details(user_id):
    userId = user_id
    success= 0
    msg = "Record Not Found"
    name=""
    mobNumber=""
    dob= ""
    adhar=""
    pan= ""
    onboarding_date = ""
    account_holder_name=""
    account_number=""
    bank_name=""
    ifsc_code=""
    branch=""
    if frappe.db.exists("User",{"name":["like","%"+userId+"%"]}):
        doc = frappe.get_doc("User",{"name":["like","%"+userId+"%"]})#{"name":["like","%"+userId+"%"]})
        success= 1
        msg = "Record Found"
        name=doc.full_name
        mobNumber=doc.mobile_no
        dob= doc.birth_date
        if frappe.db.exists("S4S User details",{"name":["like","%"+userId+"%"]}):
            usd_doc = frappe.get_doc("S4S User details",{"name":["like","%"+userId+"%"]})
            adhar=usd_doc.adhar_no
            pan= usd_doc.pan_no
            onboarding_date=usd_doc.onboarding_date
            account_holder_name=usd_doc.account_holder_name
            account_number=usd_doc.account_number
            bank_name=usd_doc.bank_name
            ifsc_code=usd_doc.ifsc_code
            branch=usd_doc.branch
    frappe.response["success"] = success
    frappe.response["message"] = msg
    frappe.response["name"] = name
    frappe.response["mobile_no"] = mobNumber
    frappe.response["dob"] = dob
    frappe.response["adhar"] = adhar
    frappe.response["pan"] = pan
    frappe.response["onboarding_date"]=onboarding_date
    frappe.response["account_holder_name"]=account_holder_name
    frappe.response["account_number"]=account_number
    frappe.response["bank_name"]=bank_name
    frappe.response["ifsc_code"]=ifsc_code
    frappe.response["branch"]=branch

# @frappe.whitelist(methods=["GET","POST","PUT"])
# def get_farmer_list(filters=None,page_no=1,kyc_status=None):
# 	pageNo = page_no
# 	kycDone=kyc_status
# 	success,msg,data,totalCount=0,"Failed",[],0
# 	conditions = ""
# 	values = {}
# 	if filters!=None:
# 		values["filters"] = "%%%s%%"%filters
# 		conditions += "(ss.supplier_name like %(filters)s or ss.mobile_no like %(filters)s)"
# 	if kycDone!=None:
# 		if kycDone == "1" or kycDone == 1:
# 			conditions += " AND (ss.supplier IS NOT NULL)" if conditions!="" else "(ss.supplier IS NOT NULL)"
# 		if kycDone == "0" or kycDone == 0:
# 			conditions += " AND (ss.supplier IS NULL)" if conditions!="" else "(ss.supplier IS NULL)"
# 	all = frappe.db.sql("""
# 		SELECT
# 			ss.name as id,
# 			ss.supplier_name as farmerName,
# 			ss.supplier as supplier_id,
# 			IF(ss.supplier IS NOT NULL,1,0) as kycDone
# 		FROM 
# 			`tabS4S Supplier` ss
# 			{0}
# 		order by ss.creation desc
# 		""".format(
# 			"WHERE "+conditions if conditions!="" else conditions
# 			# conditions 
# 		),
# 		values,
# 		as_dict=1
# 	)
# 	result = all
# 	# for i in all:
# 	# 	if i.owner == userId:
# 	# 		result.append(i)
# 	count = len(result)
# 	if not count:
# 		success = 1
# 		msg = "No Records Found"
# 	if count !=0:
# 		total_pages = math.ceil(int(count)/10)
# 		pageNo = int(pageNo) if int(pageNo)<= total_pages else total_pages
# 		result = [result[i:i+10] for i in range(0, len(result), 10)]
# 		success = 1
# 		msg = "Records Found"
# 		data = result[int(pageNo)-1]
# 		# for i in data:
# 		# 	i.pop("owner")
# 		totalCount = count
# 	print(data)
# 	frappe.response["success"] = success
# 	frappe.response["message"] = msg
# 	frappe.response["data"] = data
# 	frappe.response["total_count"] = totalCount


@frappe.whitelist(methods=["GET","POST","PUT"])
def get_farmer_form_data():
    state_list = frappe.db.sql("""SELECT s.name as state_name,"" as district_list FROM `tabS4S State` s""",as_dict=True)
    for i in state_list:
        if i["state_name"] == "Maharashtra":
            i["district_list"] = frappe.db.sql("""SELECT d.name as district_name,"" as taluka_list FROM `tabS4S District List` d""",as_dict=True)
            for j in i["district_list"]:
                j["taluka_list"] = frappe.db.sql("""SELECT t.name as taluka_name,"" as village_list FROM `tabS4S Taluka List` t where t.district = '{0}'""".format(j["district_name"]),as_dict=True)
                for k in j["taluka_list"]:
                    k["village_list"] = frappe.db.sql("""SELECT v.name as village_name FROM `tabS4S Village List` v where v.taluka = '{0}'""".format(k["taluka_name"]),as_dict=True)
        else:
            i["district_list"]=[]
    frappe.response["success"] = 1
    frappe.response["message"] = "Records Found"
    frappe.response["farmer_form_data_list"] = state_list

@frappe.whitelist(methods=["GET","POST","PUT"])
def add_farmer(name,mobile_no,taluka=None, village=None, district=None, state=None , gender=None,cc_name=None,vlcc_name=None):
    success = 0
    msg = "Failed"
    farmerId = ""
    mobNumber = mobile_no
    exists_check = 0
    if frappe.db.exists("S4S Supplier",{"mobile_no":mobile_no}):
        success = 0
        msg = "Mobile no. is already exists"
        exists_check=1
    if name and mobNumber and exists_check!=1:
        doc = frappe.new_doc("S4S Supplier")
        doc.supplier_name = name
        doc.mobile_no = mobNumber
        doc.taluka = taluka if taluka!=None else ""
        doc.village = village if village!=None else ""
        doc.district = district if district!=None else ""
        doc.state = state if state!=None else ""
        doc.gender = gender if state!=None else ""
        doc.cc_name = cc_name if cc_name!=None else ""
        doc.vlcc_name = vlcc_name if vlcc_name!=None else ""
        doc.save()
        if doc:
            success = 1
            msg = "Supplier added successfully"
            farmerId = doc.name
    frappe.response["success"] = success
    frappe.response["message"] = msg
    frappe.response["farmerId"]= farmerId

@frappe.whitelist(methods=["GET","POST","PUT"])
def get_product_list():
    success = 0
    msg = "Failed"
    items_data = []
    items_list = frappe.get_all("Item")
    for i in items_list:
        i["item_code"] = i.pop("name")
        i["item_name"] = frappe.get_value("Item",i.item_code,"item_name")
        if frappe.db.exists("Item",i.item_code):
            if frappe.db.exists("Item Price",{"item_code":i.item_code,"buying":1}):
                # doc = frappe.get_last_doc("Item Price",{"item_code":i.item_code,"buying":1})
                # i["item_buying_price"] = doc.price_list_rate
                doc = frappe.db.sql("""select name,item_code,price_list_rate,uom from `tabItem Price` where item_code = "{0}" and buying=1 order by valid_from desc, batch_no desc, uom desc""".format(i.item_code),as_dict=True)
                i["item_buying_price"] = doc[0]["price_list_rate"]
            else:
                i["item_buying_price"] =  0.00
            i["product_image"] = frappe.get_value("Item",i.item_code,"image") if frappe.get_value("Item",i.item_code,"image")!=None else ""
    if items_list:
        success = 1
        msg = "Records Found"
        items_data = items_list
    print(items_data)
    frappe.response["success"] = success
    frappe.response["message"] = msg
    frappe.response["data"] = items_data

@frappe.whitelist(methods=["GET","POST","PUT"])
def get_transaction_details(transaction_id):
    success = 0
    msg = "Record Not Found"
    transaction_details = ''
    purchase_receipt=''
    purchase_invoice=''
    stock_entry=''
    transactionId = transaction_id
    if frappe.db.exists("S4S Purchase",transactionId):
        doc = frappe.get_all("S4S Purchase",filters={"name":transactionId},fields=['name', 'supplier', 'supplier_name', 'transaction_date', 'set_warehouse', 'delivery_location', 'total_weight', 'kadta_weight', 'weight_after_kadta', 'total_amount',   's4s_farmer_query', 'kadta', 'supplier_deductions', 'grand_total',  'vlcc_name', 'cc_name', 'village', 'taluka', 'district', 'approved_status', 'vehicle_no', 'driver_name', 'assigned_vehicle', 'total_deduction_amount', 'state'])[0]
        success=1
        message="Found"
        transaction_details={key: "" if value is None else value for key, value in doc.items()}
        transaction_details["purchase_reciept_details"]=frappe.get_all("S4S Purchase receipt",filters={"parent":transaction_details["name"]},fields=["item_code","item_name","variety","moisture","rate",],order_by='idx')
        transaction_details["reciept_details"]=frappe.get_all("S4S Goni Weight",filters={"parent":transaction_details["name"]},fields=["goni_no","weight_in_kg"],order_by='idx')
        transaction_details["taxes"]=frappe.get_all("Purchase Taxes and Charges",filters={"parent":transaction_details["name"]},fields=["account_head","tax_amount"],order_by='idx')
        purchase_receipt = frappe.client.get_count("Purchase Receipt",filters={"s4s_purchase":transaction_details["name"]})
        purchase_invoice = frappe.client.get_count("Purchase Invoice",filters={"s4s_purchase":transaction_details["name"]})
        stock_entry = frappe.client.get_count("Stock Entry",filters={"s4s_purchase":transaction_details["name"]})

    frappe.response['success']=success
    frappe.response['message']=message
    frappe.response["transaction_details"]=transaction_details
    frappe.response["purchase_receipt"]=purchase_receipt
    frappe.response["purchase_invoice"]=purchase_invoice
    frappe.response["stock_entry"]=stock_entry
    # farmerName=''
    # transactionDate = ''
    # mobNumber=''
    # address=''
    # kadta=''
    # otherDeduction=''
    # products=''
    # vehicleNo=''
    # driverName=''
    # fromLocation=''
    # toLocation=''
    # farmerName=doc.supplier_name
        # transactionDate = doc.transaction_date
        # mobNumber=frappe.get_value("Supplier",doc.supplier,"mobile_no_1")
        # # address=doc.address_html
        # kadta=doc.kadta_weight
        # otherDeduction= doc.total_deduction_amount
        # products=[{ "productName": doc.purchase_receipt_details[0].item_code, "moisture": doc.purchase_receipt_details[0].moisture, "rate": doc.purchase_receipt_details[0].rate}]
        # vehicleNo=doc.vehicle_no
        # driverName=doc.driver_name
        # fromLocation=doc.set_warehouse

        # purchase_receipt=frappe.get_doc("Purchase Receipt",{"s4s_purchase":transactionId}) if frappe.db.exists("Purchase Receipt",{"s4s_purchase":transactionId}) else ""
        # purchase_invoice=frappe.get_doc("Purchase Invoice",{"s4s_purchase":transactionId}) if frappe.db.exists("Purchase Invoice",{"s4s_purchase":transactionId}) else ""
        # stock_entry=frappe.get_doc("Stock Entry",{"s4s_purchase":transactionId}) if frappe.db.exists("Stock Entry",{"s4s_purchase":transactionId}) else ""
    # frappe.response['farmerName']=farmerName
    # frappe.response['transactionDate']=transactionDate
    # frappe.response['mobNumber']=mobNumber
    # frappe.response['address']=address
    # frappe.response['kadta']=kadta
    # frappe.response['otherDeduction']=otherDeduction
    # frappe.response['products']=products
    # frappe.response['vehicleNo']=vehicleNo
    # frappe.response['driverName']=driverName
    # frappe.response['fromLocation']=fromLocation
    # frappe.response['toLocation']=toLocation
        # toLocation=

@frappe.whitelist(methods=["GET","POST","PUT"])
def get_inquiry_details(inquiry_id):
    success=0
    message='Not Found'
    inquiryId=inquiry_id
    # productName=''
    # type=''
    # grade=''
    # moisture=''
    # ratePerQty=''
    # kadta=''
    # otherDeduction=''
    # totalRate=''
    imquiry_details = []
    farmer_details = []
    if frappe.db.exists("S4S Farmer Query",inquiryId):
        doc = frappe.get_doc("S4S Farmer Query",inquiryId,["supplier"])
        doc = frappe.get_all("S4S Farmer Query",filters={'name':inquiryId},fields=[ "supplier", "supplier_name", "item_code", "item_name", "variety", "moisture", "rate", "product_photo", "delivery_location", "tentative_qty", "sample_given", "date", "mobile_no", "vlcc_name", "cc_name", "village", "taluka", "district", "state", "pickup_request", "comment", "s4s_purchase", "vehicle_no", "driver_name", "assigned_vehicle"])
        success=1
        message="Found"
        # productName=doc.item_code
        # var_type=doc.variety
        # grade=""
        # moisture=doc.moisture
        # ratePerQty=doc.rate
        # kadta=""
        # otherDeduction=""
        # totalRate=""
        inquiry_details  = doc[0]
        fq = frappe.get_doc("S4S Supplier",doc[0]["supplier"])
        if fq.supplier:
            kyc_status = 1
        elif not fq.supplier and (fq.account_holder_name and fq.account_number and fq.bank_name and fq.ifsc_code and fq.branch):
            kyc_status = 2
        elif not fq.supplier and (not fq.account_holder_name or not fq.account_number or not fq.bank_name or not fq.ifsc_code or not fq.branch):		
            kyc_status = 0
        else:
            kyc_status = ""
        farmer_details = [{
            "id": fq.name,
            "farmer_name": fq.supplier_name,
            "supplier_id": fq.supplier,
            "kyc_status": kyc_status
        }]
    for key, value in inquiry_details.items():
        if value is None:
            inquiry_details[key] = ""
    frappe.response['success']=success
    frappe.response['message']=message
    # frappe.response['productName']=productName
    # frappe.response['variety_type']=var_type
    # frappe.response['grade']=grade
    # frappe.response['moisture']=moisture
    # frappe.response['ratePerQty']=ratePerQty
    # frappe.response['kadta']=kadta
    # frappe.response['otherDeduction']=otherDeduction
    # frappe.response['totalRate']=totalRate
    frappe.response['inquiry_details']=inquiry_details
    frappe.response['farmer_details']=farmer_details
    # return inquiry_details

@frappe.whitelist(methods=["GET","POST","PUT"])
def add_transaction(user_id,params):
    success = 0
    msg = "Failed"
    if type(params) != str:
        params = json.dumps(params)
    params = json.loads(params)
    if user_id and frappe.db.exists("S4S User details",user_id):
        params["set_warehouse"] = frappe.get_doc("S4S User details",user_id).inward_warehouse
        if params["set_warehouse"] and params["set_warehouse"]!="":
            print()
            if params["supplier"] and params["supplier"]!="" and frappe.db.exists("Supplier",params["supplier"]):
                supplier = frappe.get_doc("Supplier",params["supplier"])
                params["supplier_name"]=supplier.supplier_name
                params["vlcc_name"]=supplier.vlcc_name
                params["cc_name"]=supplier.cc_name
                params["village"]=supplier.village
                params["taluka"]=supplier.taluka
                params["district"]=supplier.district
                params["state"]=supplier.state_
                if params["purchase_receipt_details"]:
                    for i in params["purchase_receipt_details"]:
                        if i["item_code"] and frappe.db.exists("Item",i["item_code"]):
                            i["item_name"]=frappe.get_doc("Item",i["item_code"]).item_name
                        else:
                            success = 0
                            msg = "Item code {0} is not exists".format(i["item_code"])
                print(params) 
                params["doctype"] = "S4S Purchase"
                new_doc = frappe.get_doc(params)
                new_doc.save()
                if new_doc:
                    success = 1
                    msg = "Transaction submitted successfully"      
            else:
                success = 0
                msg = "Supplier {0} is not exists".format(params["supplier"])
        else:
            success = 0
            msg = "Inward warehouse is not set.Please contact to Admin."
    
    frappe.response['success']=success
    frappe.response['message']=msg

        # params["supplier_deductions"]="Supplier Deduction - SFSTS"
        # if params["taxes"]:
        # 	tax_temp = frappe.get_doc("Purchase Taxes and Charges Template","Supplier Deduction - SFSTS")
        # 	tax_tab = []
        # 	for i in tax_temp.taxes:
        # 		tax = frappe.db.sql("""
        # 			SELECT
        # 				pt.category as category,
        # 				pt.add_deduct_tax as add_deduct_tax,
        # 				pt.charge_type as charge_type,
        # 				pt.included_in_print_rate as included_in_print_rate,
        # 				pt.included_in_paid_amount as included_in_paid_amount,
        # 				pt.account_head as account_head,
        # 				pt.description as description,
        # 				pt.rate as rate,
        # 				pt.cost_center as cost_center,
        # 				pt.account_currency as account_currency,
        # 				pt.tax_amount as tax_amount,
        # 				pt.tax_amount_after_discount_amount as tax_amount_after_discount_amount,
        # 				pt.total as total,
        # 				pt.base_tax_amount as base_tax_amount,
        # 				pt.base_total as base_total,
        # 				pt.base_tax_amount_after_discount_amount as base_tax_amount_after_discount_amount
        # 			FROM 
        # 				`tabPurchase Taxes and Charges` pt
        # 			WHERE
        # 				pt.name = '{0}'
        # 		""".format(i.name),as_dict=True)
        # 		tax_tab.append(tax[0])
        # 	for i in tax_tab:
        # 		for j in params["taxes"]:
        # 			if i.account_head == j["account_head"]:
        # 				i.tax_amount = j["amount"]
        # 	# print(tax_tab)
        # params["taxes"]=tax_tab


    #     params["doctype"] = "S4S Purchase"
    #     new_doc = frappe.get_doc(params)
    #     new_doc.save()
    #     if new_doc:
    #         success = 1
    #         msg = "Transaction submitted successfully"
    #     # return new_doc
    
    # except HTTPError as http_err:
    #     print(f'HTTP error occurred: {http_err}')
    # except Exception as err:
    #     print(f'Other error occurred: {err}')
    
    # frappe.response['success']=success
    # frappe.response['message']=msg

@frappe.whitelist(methods=["GET","POST","PUT"])
def add_inquiry(params):
    success = 0
    msg = "Failed"
    # try:
    if type(params) != str:
        params = json.dumps(params)
    params = json.loads(params)
    if params["supplier"] and params["supplier"]!="" and frappe.db.exists("S4S Supplier",params["supplier"]):
        supplier = frappe.get_doc("S4S Supplier",params["supplier"])
        params["supplier_name"]=supplier.supplier_name
        params["vlcc_name"]=supplier.vlcc_name
        params["cc_name"]=supplier.cc_name
        params["village"]=supplier.village
        params["taluka"]=supplier.taluka
        params["district"]=supplier.district
        params["state"]=supplier.state
        params["mobile_no"]=supplier.mobile_no
        if params["item_code"] and frappe.db.exists("Item",params["item_code"]):
            params["item_name"]=frappe.get_doc("Item",params["item_code"]).item_name
            params["doctype"] = "S4S Farmer Query"
            new_doc = frappe.get_doc(params)
            new_doc.flags.ignore_permissions = True
            new_doc.save()
            if new_doc:
                success = 1
                msg = "Inquiry submitted successfully"

        else:
            success = 0
            msg = "Item code {0} is not exists".format(params["item_code"])
    else:
        success = 0
        msg = "Farmer {0} is not exists.".format(params["supplier"])

    # **********************
    files = frappe.request.files
    is_private = 1
    doctype = "S4S Farmer Query"
    docname = new_doc.name
    fieldname = ""
    file_url = frappe.form_dict.file_url
    folder = frappe.form_dict.folder or "Home"
    method = frappe.form_dict.method
    filename = frappe.form_dict.file_name
    content = None
    product_photo = ""
    if new_doc.name and frappe.db.exists("S4S Farmer Query",new_doc.name):
        if "product_photo" in files:
            file = files["product_photo"]
            content = file.stream.read()
            filename = file.filename
            frappe.local.uploaded_file = content
            frappe.local.uploaded_filename = filename
            fieldname = "product_photo"
            ret = frappe.get_doc(
                {
                    "doctype": "File",
                    "attached_to_doctype": doctype,
                    "attached_to_name": docname,
                    "attached_to_field": fieldname,
                    "folder": folder,
                    "file_name": filename,
                    "file_url": file_url,
                    "is_private": is_private,
                    "content": content
                }
            )
            ret.save()
            product_photo=ret.file_url
    if product_photo!="":
        new_doc.product_photo = product_photo
        new_doc.save()
        # ********************
    
    # except HTTPError as http_err:
    # 	print(f'HTTP error occurred: {http_err}')
    # except Exception as err:
    # 	print(f'Other error occurred: {err}')
    frappe.response['success']=success
    frappe.response['message']=msg

@frappe.whitelist(methods=["PUT"])
def add_kyc(farmer_id,params=None):
    success = 0
    msg = "Failed To Add KYC"
    farmerId = farmer_id
    files = frappe.request.files
    is_private = 1
    doctype = "S4S Supplier"
    docname = farmerId
    fieldname = ""
    file_url = frappe.form_dict.file_url
    folder = frappe.form_dict.folder or "Home"
    method = frappe.form_dict.method
    filename = frappe.form_dict.file_name
    content = None
    pan_file,adhar_file,passbook_file = "","",""
    if farmerId and frappe.db.exists("S4S Supplier",farmerId):
        if "pan" in files:
            file = files["pan"]
            content = file.stream.read()
            filename = farmerId+"-"+file.filename
            frappe.local.uploaded_file = content
            frappe.local.uploaded_filename = filename
            fieldname = "pan_card_photo"
            ret = frappe.get_doc(
                {
                    "doctype": "File",
                    "attached_to_doctype": doctype,
                    "attached_to_name": docname,
                    "attached_to_field": fieldname,
                    "folder": folder,
                    "file_name": filename,
                    "file_url": file_url,
                    "is_private": is_private,
                    "content": content
                }
            )
            ret.save()
            pan_file=ret.file_url
            
        if "adhar" in files:
            file = files["adhar"]
            content = file.stream.read()
            filename = farmerId+"-"+file.filename
            frappe.local.uploaded_file = content
            frappe.local.uploaded_filename = filename
            fieldname = "aadhar_card_photo"
            ret = frappe.get_doc(
                {
                    "doctype": "File",
                    "attached_to_doctype": doctype,
                    "attached_to_name": docname,
                    "attached_to_field": fieldname,
                    "folder": folder,
                    "file_name": filename,
                    "file_url": file_url,
                    "is_private": is_private,
                    "content": content
                }
            )
            ret.save()
            adhar_file=ret.file_url

        if "bank_passbook" in files:
            file = files["bank_passbook"]
            content = file.stream.read()
            filename = farmerId+"-"+file.filename
            frappe.local.uploaded_file = content
            frappe.local.uploaded_filename = filename
            fieldname = "bank_passbook_photo"
            ret = frappe.get_doc(
                {
                    "doctype": "File",
                    "attached_to_doctype": doctype,
                    "attached_to_name": docname,
                    "attached_to_field": fieldname,
                    "folder": folder,
                    "file_name": filename,
                    "file_url": file_url,
                    "is_private": is_private,
                    "content": content
                }
            )
            
            ret.save()
            passbook_file=ret.file_url

        if params!=None:
            if type(params) != str:
                params = json.dumps(params)
            params = json.loads(params)
            # params["doctype"] = "S4S Supplier"
            # params["name"]=farmerId
            doc = frappe.get_doc("S4S Supplier",farmerId)
            if pan_file!="":
                params["pan_card_photo"] = pan_file
            if adhar_file!="":
                params["aadhar_card_photo"] = adhar_file
            if passbook_file!="":
                params["bank_passbook_photo"] = passbook_file
            doc.update(params)
            doc.save()

        success = 1
        msg = "Kyc submitted successfully waiting for approval"
    frappe.response['success']=success
    frappe.response['message']=msg

@frappe.whitelist(methods="GET")
def get_transaction_form_data():
    # farmerId = farmer_id
    success= 0
    msg = "Record Not Found"
    # supplier_id=""
    # name=""
    # mobNumber=""
    # gender= ""
    # taluka=""
    # state= ""
    # district=""
    # village=""
    # cc=""
    # vlcc = ""
    # inward_warehouse = ""
    items_data = []
    deduction_data =[]
    packaging_data=[]
    # if frappe.db.exists("S4S Supplier",{"name":["like","%"+farmerId+"%"],"type_of_supplier":"Farmer"}):
    #     doc = frappe.get_doc("S4S Supplier",{"name":["like","%"+farmerId+"%"],"type_of_supplier":"Farmer"})
    #     success= 1
    #     msg = "Record Found"
    #     supplier_id = doc.supplier
    #     name=doc.supplier_name
    #     mobNumber=doc.mobile_no
    #     gender= doc.gender
    #     taluka=doc.taluka
    #     state= doc.state
    #     district=doc.district
    #     village=doc.village
    #     cc=doc.cc_name
    #     vlcc = doc.vlcc_name
        # if frappe.db.exists("S4S User details",user_id):
        #     inward_warehouse = frappe.get_value("S4S User details",user_id,"inward_warehouse")
    items_data = frappe.get_all("Item",["item_code","item_name"])
    for i in items_data:
        if frappe.db.exists("Item",i.item_code):
            if frappe.db.exists("Item Price",{"item_code":i.item_code,"buying":1}):
                # doc = frappe.get_last_doc("Item Price",{"item_code":i.item_code,"buying":1})
                # i["item_buying_price"] = doc.price_list_rate
                doc = frappe.db.sql("""select name,item_code,price_list_rate,uom from `tabItem Price` where item_code = "{0}" and buying=1 order by valid_from desc, batch_no desc, uom desc""".format(i.item_code),as_dict=True)
                i["item_buying_price"] = doc[0]["price_list_rate"]
            else:
                i["item_buying_price"] =  0.00
            i["product_image"] = frappe.get_value("Item",i.item_code,"image") if frappe.get_value("Item",i.item_code,"image")!=None else ""
    
    if frappe.db.exists("Purchase Taxes and Charges Template","Supplier Deduction - SFSTS"):
        taxes_doc = frappe.get_doc("Purchase Taxes and Charges Template","Supplier Deduction - SFSTS")
        if taxes_doc.taxes:
            for k in taxes_doc.taxes:
                deduction_data.append({
                    "account_head":k.account_head
                })
    packaging_data = frappe.get_all("S4S Goni No",fields=["name"],order_by = "name desc")
    for i in packaging_data:
        i["packaging_name"] = i.pop("name")
    
    if items_data or packaging_data or deduction_data:
        success= 1
        msg = "Record Found"

    frappe.response["success"] = success
    frappe.response["message"] = msg
    # frappe.response["supplier_id"]=supplier_id
    # frappe.response["name"] = name
    # frappe.response["mobile_no"] = mobNumber
    # frappe.response["gender"] = gender
    # frappe.response["taluka"] = taluka
    # frappe.response["state"] = state
    # frappe.response["district"] = district
    # frappe.response["village"] = village
    # frappe.response["cc"] = cc
    # frappe.response["vlcc"]=vlcc
    # frappe.response["inward_warehouse"]=inward_warehouse
    frappe.response["data"] = items_data
    frappe.response["packaging_data"]=packaging_data
    frappe.response["deduction_data"]=deduction_data

@frappe.whitelist(methods="GET")
def get_kyc_form_data():
    bank_data = frappe.get_all("S4S Bank List")
    frappe.response["success"] = 1
    frappe.response["message"] = "Found"
    frappe.response["data"] = bank_data

@frappe.whitelist(methods="GET")
def get_inquiry_form_data(farmer_id):
    farmerId = farmer_id
    success= 0
    msg = "Record Not Found"
    name=""
    mobNumber=""
    gender= ""
    taluka=""
    state= ""
    district=""
    village=""
    cc=""
    vlcc = ""
    items_data = []
    if frappe.db.exists("S4S Supplier",{"name":["like","%"+farmerId+"%"],"type_of_supplier":"Farmer"}):
        doc = frappe.get_doc("S4S Supplier",{"name":["like","%"+farmerId+"%"],"type_of_supplier":"Farmer"})
        success= 1
        msg = "Record Found"
        name=doc.supplier_name
        mobNumber=doc.mobile_no
        gender= doc.gender
        taluka=doc.taluka
        state= doc.state
        district=doc.district
        village=doc.village
        cc=doc.cc_name
        vlcc = doc.vlcc_name
        items_data = frappe.get_all("Item",["item_code","item_name"])
        for i in items_data:
            if frappe.db.exists("Item",i.item_code):
                if frappe.db.exists("Item Price",{"item_code":i.item_code,"buying":1}):
                    # doc = frappe.get_last_doc("Item Price",{"item_code":i.item_code,"buying":1})
                    # i["item_buying_price"] = doc.price_list_rate
                    doc = frappe.db.sql("""select name,item_code,price_list_rate,uom from `tabItem Price` where item_code = "{0}" and buying=1 order by valid_from desc, batch_no desc, uom desc""".format(i.item_code),as_dict=True)
                    i["item_buying_price"] = doc[0]["price_list_rate"]
                else:
                    i["item_buying_price"] =  0.00
                i["product_image"] = frappe.get_value("Item",i.item_code,"image") if frappe.get_value("Item",i.item_code,"image")!=None else ""
    frappe.response["success"] = success
    frappe.response["message"] = msg
    # frappe.response["name"] = name
    # frappe.response["mobile_no"] = mobNumber
    # frappe.response["gender"] = gender
    # frappe.response["taluka"] = taluka
    # frappe.response["state"] = state
    # frappe.response["district"] = district
    # frappe.response["village"] = village
    # frappe.response["cc"] = cc
    # frappe.response["vlcc"]=vlcc
    frappe.response["product_list"] = items_data


@frappe.whitelist(methods=["GET","POST","PUT"])
def get_delivery_challan_list(user_id,stock_entry_id=None,transaction_id=None,page_po=1):
    success,msg,data,totalCount=0,"Failed",[],0
    userId = user_id
    stock_entryId = stock_entry_id
    transactionId = transaction_id
    pageNo = page_po
    filters = stock_entryId
    conditions = ""
    values = {"userId":userId}
    if filters!=None:
        values["filters"] = "%%%s%%"%filters
        conditions += "se.name like %(filters)s"
    if transactionId!=None:
        values["transactionId"] = "%%%s%%"%transactionId
        conditions += "or se.s4s_purchase like %(transactionId)s" if conditions!="" else " se.s4s_purchase like %(transactionId)s"
    print(conditions)
    result = frappe.db.sql("""
        SELECT
            se.name as stock_entry_id,
            se.s4ssupplier as approved_supplier_id,
            s.supplier_name as supplier_name,
            se.stock_entry_type as stock_entry_type
        FROM 
            `tabStock Entry` se
        JOIN
            `tabSupplier` s ON se.s4ssupplier = s.name
        WHERE
            se.owner = "{0}"
            {1}
        ORDER BY
            se.creation DESC
        """.format(userId,
            "AND ("+conditions+" )" if conditions!="" else conditions 
        ),
        values,
        as_dict=1
    )
    count = len(result)
    if not count:
        success = 1
        msg = "No Records Found"
    if count !=0:
        total_pages = math.ceil(int(count)/10)
        pageNo = int(pageNo) if int(pageNo)<= total_pages else total_pages
        result = [result[i:i+10] for i in range(0, len(result), 10)]
        success = 1
        msg = "Records Found"
        data = result[int(pageNo)-1]
        totalCount = count
    frappe.response["success"] = success
    frappe.response["message"] = msg
    frappe.response["data"] = data
    frappe.response["totalCount"] = totalCount

@frappe.whitelist(methods=["GET","POST","PUT"])
def get_delivery_challan_details(challan_id):
    success= 0
    msg = "Record Not Found"
    data=""
    if challan_id and frappe.db.exists("Stock Entry",challan_id):
        success= 1
        msg = "Record Found"
        data = frappe.get_doc("Stock Entry",challan_id)
    frappe.response["success"] = success
    frappe.response["message"] = msg
    frappe.response["challan_details"] = data

@frappe.whitelist(methods=["GET","POST","PUT"])
def get_purchase_receipt_list(user_id,filters=None,transaction_id=None,page_no=1):
    success,msg,data,totalCount=0,"Failed",[],0
    userId = user_id
    # purchase_receiptId = purchase_receipt_id
    transactionId = transaction_id
    pageNo = page_no
    # filters = purchase_receiptId
    conditions = ""
    values = {"userId":userId}
    role = ""
    no_role = 0
    if "CC User" in frappe.get_roles(userId):
        role = 'pr.owner="{0}"'.format(userId)
        if frappe.db.exists("S4S User details",userId):
            get_usd = frappe.get_doc("S4S User details",userId)
            if get_usd.inward_warehouse:
                role+=' OR pr.set_warehouse="{0}"'.format(get_usd.inward_warehouse)
        role = "("+role+")"
    elif "VLCC User" in frappe.get_roles(userId):
        print()
        if not transaction_id:
            role = '(pr.owner="{0}" or pr.owner!="{0}")'.format(userId)
        else:
            role = '(pr.owner="{0}")'.format(userId)
    # elif "ME Field Executive" in frappe.get_roles(userId):
    # 	pass
    else:
        no_role = 1
    
    if filters!=None:
        values["filters"] = "%%%s%%"%filters
        conditions += "(pr.name like %(filters)s or pr.supplier_name like %(filters)s)"
    if transactionId!=None:
        values["transactionId"] = "%%%s%%"%transactionId
        conditions += "or pr.s4s_purchase like %(transactionId)s" if conditions!="" else " pr.s4s_purchase like %(transactionId)s"
    if no_role!=1:
        result = frappe.db.sql("""
            SELECT
                pr.name as purchase_receipt_id,
                pr.supplier as approved_supplier_id,
                pr.supplier_name as supplier_name
            FROM 
                `tabPurchase Receipt` pr
            WHERE
                {0}
                {1}
            ORDER BY
                pr.creation DESC
            """.format(role,
                "AND ("+conditions+" )" if conditions!="" else conditions 
            ),
            values,
            as_dict=1
        )
        count = len(result)
        if not count:
            success = 1
            msg = "No Records Found"
        if count !=0:
            total_pages = math.ceil(int(count)/10)
            pageNo = int(pageNo) if int(pageNo)<= total_pages else total_pages
            result = [result[i:i+10] for i in range(0, len(result), 10)]
            success = 1
            msg = "Records Found"
            data = result[int(pageNo)-1]
            totalCount = count
    else:
        success = 1
        msg = "Records Not Found.User does not have any role in CC,VLCC,ME"
    frappe.response["success"] = success
    frappe.response["message"] = msg
    frappe.response["data"] = data
    frappe.response["total_count"] = totalCount


@frappe.whitelist(methods=["GET","POST","PUT"])
def get_purchase_invoice_list(user_id,filters=None,transaction_id=None,page_no=1):
    success,msg,data,totalCount=0,"Failed",[],0
    userId,transactionId,pageNo,conditions = user_id,transaction_id,page_no,""
    # filters = purchase_invoiceId
    values = {"userId":userId}
    role = ""
    no_role = 0
    if "CC User" in frappe.get_roles(userId):
        role = 'pi.owner="{0}"'.format(userId)
        if frappe.db.exists("S4S User details",userId):
            get_usd = frappe.get_doc("S4S User details",userId)
            if get_usd.inward_warehouse:
                role+=' OR pi.set_warehouse="{0}"'.format(get_usd.inward_warehouse)
        role = "("+role+")"
    elif "VLCC User" in frappe.get_roles(userId):
        print()
        if not transaction_id:
            role = '(pi.owner="{0}" or pi.owner!="{0}")'.format(userId)
        else:
            role = '(pi.owner="{0}")'.format(userId)
        # role = 'pi.owner="{0}"'.format(userId)
    # elif "ME Field Executive" in frappe.get_roles(userId):
    # 	pass
    else:
        no_role = 1
    print(role)
    if filters!=None:
        values["filters"] = "%%%s%%"%filters
        conditions += "(pi.name like %(filters)s or pi.supplier_name like  %(filters)s)"
    if transactionId!=None:
        values["transactionId"] = "%%%s%%"%transactionId
        conditions += "or pi.s4s_purchase like %(transactionId)s" if conditions!="" else " pi.s4s_purchase like %(transactionId)s"
    # print(conditions)
    if no_role!=1:
        result = frappe.db.sql("""
            SELECT
                pi.name as purchase_invoice_id,
                pi.supplier as approved_supplier_id,
                pi.supplier_name as supplier_name
            FROM 
                `tabPurchase Invoice` pi
            WHERE
                {0}
                {1}
            ORDER BY
                pi.creation DESC
            """.format(role,
                "AND ("+conditions+" )" if conditions!="" else conditions 
            ),
            values,
            as_dict=1
        )
        count = len(result)
        if not count:
            success = 1
            msg = "No Records Found"
        if count !=0:
            total_pages = math.ceil(int(count)/10)
            pageNo = int(pageNo) if int(pageNo)<= total_pages else total_pages
            result = [result[i:i+10] for i in range(0, len(result), 10)]
            success = 1
            msg = "Records Found"
            data = result[int(pageNo)-1]
            totalCount = count
    else:
        success = 1
        msg = "Records Not Found.User does not have any role in CC,VLCC,ME"
    frappe.response["success"] = success
    frappe.response["message"] = msg
    frappe.response["data"] = data
    frappe.response["total_count"] = totalCount


@frappe.whitelist(methods=["GET","POST","PUT"])
def get_farmer_list(user_id,filters=None,page_no=1,kyc_status=None):
    pageNo = page_no
    kycDone=kyc_status
    success,msg,data,totalCount=0,"Failed",[],0
    conditions,filt_condition_cc,filt_condition_vlcc = "","",""
    values = {}
    cc_str,vlcc_str = "",""
    final_condition = ""
    cc_list,vlcc_list=[],[]
    if frappe.db.exists("User Permission",{"user":user_id}):
        vlcc_list=[x["for_value"] for x in frappe.get_all("User Permission",{"user":user_id,"allow":"S4S VLCC List"},["for_value"])]
        cc_list = [x["for_value"] for x in frappe.get_all("User Permission",{"user":user_id,"allow":"S4S CC List"},["for_value"])]
        # print(vlcc_list,cc_list,"print1")
    # 	if vlcc_list:
    # 		# print(vlcc_list,"print2")
    # 		for i in all:
    # 			if i.vlcc in vlcc_list:
    # 				result.append(i)
    # 				all.remove(i)
    # 	if cc_list:
    # 		for i in all:
    # 			print(i.cc,cc_list)
    # 			if i.cc in cc_list:
    # 				# print(i,cc_list,"print3")
    # 				result.append(i)
    # 				all.remove(i)
    # else:
    # 	result=all
    # if frappe.db.exists("S4S User details",user_id):
    # 	user_doc = frappe.get_doc("S4S User details",user_id)
    # 	if user_doc.assign_cc:
    # 		cc_list = [x.cc_name for x in user_doc.assign_cc]
    # 	if user_doc.assign_vlcc:
    # 		vlcc_list = [x.vlcc_name for x in user_doc.assign_vlcc]
    if cc_list:
        for i in cc_list:
            if cc_str=="":
                cc_str+='"'+i+'"'
            else:
                cc_str+=',"'+i+'"'
    if cc_str!="":
        cc_str="("+cc_str+")"
        filt_condition_cc += " ss.cc_name IN {0} ".format(cc_str)

    if vlcc_list:
        for i in vlcc_list:
            if vlcc_str=="":
                vlcc_str+='"'+i+'"'
            else:
                vlcc_str+=',"'+i+'"'
    if vlcc_str!="":
        vlcc_str="("+vlcc_str+")"
        filt_condition_vlcc += " ss.vlcc_name IN {0} ".format(vlcc_str)

    if filt_condition_cc!="" and filt_condition_cc!=None:
        final_condition+= ' '+filt_condition_cc+' '
    if filt_condition_vlcc!="" and filt_condition_vlcc!=None:
        final_condition+= ' OR '+filt_condition_vlcc if final_condition!="" else ' '+filt_condition_vlcc+' '

    final_condition= '('+final_condition+')' if final_condition!="" else ""
    if filters!=None:
        values["filters"] = "%%%s%%"%filters
        conditions += "(ss.supplier_name like %(filters)s or ss.mobile_no like %(filters)s)"
    print(conditions,final_condition)
    if kycDone == "0" or kycDone == 0:
        all = frappe.db.sql("""
            SELECT 
                ss.name as id,ss.supplier_name as farmer_name,ss.mobile_no as mobile_no,ss.village as village,ss.supplier as supplier_id,ss.gender, ss.taluka, ss.district,ss.state, ss.cc_name as cc, ss.vlcc_name as vlcc ,0 as kyc_status
            FROM 
                `tabS4S Supplier` ss
            WHERE
                ss.supplier IS NULL AND (ss.account_holder_name IS NULL OR ss.account_number IS NULL OR ss.bank_name IS NULL OR ss.ifsc_code IS NULL OR ss.branch IS NULL)
                {0}{1}
            order by ss.creation desc
        """.format("AND "+conditions if conditions!="" else conditions," AND "+final_condition if final_condition!="" else final_condition),values,as_dict=1)
    elif kycDone == "1" or kycDone == 1:
        all = frappe.db.sql("""
            SELECT 
                ss.name as id,ss.supplier_name as farmer_name,ss.mobile_no as mobile_no,ss.village as village,ss.supplier as supplier_id,ss.gender, ss.taluka, ss.district,ss.state, ss.cc_name as cc, ss.vlcc_name as vlcc ,1 as kyc_status
            FROM 
                `tabS4S Supplier` ss
            WHERE
                ss.supplier IS NOT NULL
                {0}{1}
            order by ss.creation desc
        """.format(" AND "+conditions if conditions!="" else conditions," AND "+final_condition if final_condition!="" else final_condition),values,as_dict=1)
    elif kycDone == "2" or kycDone == 2:
        all = frappe.db.sql("""
            SELECT 
                ss.name as id,ss.supplier_name as farmer_name,ss.mobile_no as mobile_no,ss.village as village,ss.supplier as supplier_id,ss.gender, ss.taluka, ss.district,ss.state, ss.cc_name as cc, ss.vlcc_name as vlcc ,2 as kyc_status
            FROM 
                `tabS4S Supplier` ss
            WHERE
                ss.supplier IS NULL AND (ss.account_holder_name IS NOT NULL OR ss.account_number IS NOT NULL OR ss.bank_name IS NOT NULL OR ss.ifsc_code IS NOT NULL OR ss.branch IS NOT NULL)
                {0}{1}
            order by ss.creation desc
        """.format(" AND "+conditions if conditions!="" else conditions," AND "+final_condition if final_condition!="" else final_condition),values,as_dict=1)

                # WHEN ss.supplier IS NULL AND (ss.account_holder_name IS NULL OR ss.account_number IS NULL OR ss.bank_name IS NULL OR ss.ifsc_code IS NULL OR ss.branch IS NULL) THEN 0
    else:
        all = frappe.db.sql("""
            SELECT
                ss.name as id,
                ss.supplier_name as farmer_name,
                ss.mobile_no as mobile_no,
                ss.village as village,
                ss.supplier as supplier_id,
                ss.gender, ss.taluka, ss.district,ss.state, ss.cc_name as cc, ss.vlcc_name as vlcc,
                CASE
                    WHEN ss.supplier IS NOT NULL THEN 1
                    WHEN ss.supplier IS NULL AND (ss.account_holder_name IS NOT NULL AND ss.account_number IS NOT NULL AND ss.bank_name IS NOT NULL AND ss.ifsc_code IS NOT NULL AND ss.branch IS NOT NULL) THEN 2
                    WHEN ss.supplier IS NULL AND (ss.account_holder_name IS NULL OR ss.account_number IS NULL OR ss.bank_name IS NULL OR ss.ifsc_code IS NULL OR ss.branch IS NULL) THEN 0
                END AS kyc_status
            FROM 
                `tabS4S Supplier` ss
            WHERE
                ss.name IS NOT NULL
                {0}{1}
            order by ss.creation desc
            """.format(
            " AND "+conditions if conditions!="" else conditions," AND "+final_condition if final_condition!="" else final_condition
            # conditions 
        ),values,as_dict=1)
    result = all
    # result = []
    # for i in all:
    # if i.owner == user_id:
    # 	result.append(i)
        # pass
    count = len(result)
    if not count:
        success = 1
        msg = "No Records Found"
    if count !=0:
        total_pages = math.ceil(int(count)/10)
        pageNo = int(pageNo) if int(pageNo)<= total_pages else total_pages
        result = [result[i:i+10] for i in range(0, len(result), 10)]
        success = 1
        msg = "Records Found"
        data = result[int(pageNo)-1]
        # for i in data:
        # 	i.pop("owner")
        totalCount = count
    frappe.response["success"] = success
    frappe.response["message"] = msg
    frappe.response["data"] = data
    frappe.response["total_count"] = totalCount

    frappe.response["vlcc_list"]=vlcc_list
    frappe.response["cc_list"]=cc_list

# @frappe.whitelist(methods=["GET","POST","PUT"])
# def get_payment_entry_list(user_id,filters=None,page_no=1):
# 	success,msg,data,totalCount=0,"Failed",[],0
# 	userId,pageNo,conditions = user_id,page_no,""
# 	# filters = purchase_invoiceId
# 	values = {"userId":userId}
# 	role = ""
# 	no_role = 0
# 	if "CC User" in frappe.get_roles(userId):
# 		role = 'pe.owner="{0}"'.format(userId)
# 		# if frappe.db.exists("S4S User details",userId):
# 		# 	get_usd = frappe.get_doc("S4S User details",userId)
# 		# 	if get_usd.inward_warehouse:
# 		# 		role+=' OR pe.set_warehouse="{0}"'.format(get_usd.inward_warehouse)
# 		# role = "("+role+")"
# 	elif "VLCC User" in frappe.get_roles(userId):
# 		role = 'pe.owner="{0}"'.format(userId)
# 	# elif "ME Field Executive" in frappe.get_roles(userId):
# 	# 	pass
# 	else:
# 		no_role = 1
# 	if filters!=None:
# 		values["filters"] = "%%%s%%"%filters
# 		conditions += "(pe.name like %(filters)s or pe.party_name like  %(filters)s)"
# 	# if transactionId!=None:
# 	# 	values["transactionId"] = "%%%s%%"%transactionId
# 	# 	conditions += "or pi.s4s_purchase like %(transactionId)s" if conditions!="" else " pi.s4s_purchase like %(transactionId)s"
# 	# print(conditions)
# 	if no_role!=1:
# 		result = frappe.db.sql("""
# 			SELECT
# 				pe.name as payment_entry_id,
# 				pe.party as approved_supplier_id,
# 				pe.party_name as supplier_name,
# 				pe.s4s_purchase as s4s_purchase_id
# 			FROM 
# 				`tabPayment Entry` pe
# 			WHERE
# 				{0}
# 				{1}
# 			ORDER BY
# 				pe.creation DESC
# 			""".format(role,
# 				"AND ("+conditions+" )" if conditions!="" else conditions 
# 			),
# 			values,
# 			as_dict=1
# 		)
# 		count = len(result)
# 		if not count:
# 			success = 1
# 			msg = "No Records Found"
# 		if count !=0:
# 			total_pages = math.ceil(int(count)/10)
# 			pageNo = int(pageNo) if int(pageNo)<= total_pages else total_pages
# 			result = [result[i:i+10] for i in range(0, len(result), 10)]
# 			success = 1
# 			msg = "Records Found"
# 			data = result[int(pageNo)-1]
# 			totalCount = count
# 	else:
# 		success = 1
# 		msg = "Records Not Found.User does not have any role in CC,VLCC,ME"
# 	frappe.response["success"] = success
# 	frappe.response["message"] = msg
# 	frappe.response["data"] = data
# 	frappe.response["total_count"] = totalCount
from frappe.permissions import get_user_permissions,get_allowed_docs_for_doctype

@frappe.whitelist(methods=["GET", "POST", "PUT"])
def get_payment_entry_list(user_id="krishnakadam.moomba@gmail.com",filters=None, page_no=1):
    document_type = "Payment Entry"
    fields = ["name as payment_entry_id","party as approved_supplier_id","party_name as supplier_name","s4s_purchase as s4s_purchase_id"]
    condition = None
    success, msg, data, total_count = 0, "Failed", [], 0
    # permitted_doctypes = get_user_permissions(user_id)
    # print(permitted_doctypes,type(permitted_doctypes["S4S CC List"][0]))
    # get_per_doc = get_allowed_docs_for_doctype(permitted_doctypes["S4S CC List"],document_type)
    # print(get_per_doc)
    # if document_type not in permitted_doctypes:
    #     frappe.throw("Access denied for the specified doctype.")

    if filters:
        condition = [
            f"(`tab{document_type}`.`name` like '%{filters}%') or (`tab{document_type}`.`party_name` like '%{filters}%')"
        ]
    print(frappe.get_list(document_type))
    result = get_all(doctype=document_type, filters=condition, fields=fields,order_by="creation desc")
    count = len(result)

    if count == 0:
        success = 1
        msg = "No Records Found"
    else:
        total_pages = math.ceil(count / 10)
        page_no = min(int(page_no), total_pages)
        paginated_result = [result[i:i + 10] for i in range(0, count, 10)]
        data = paginated_result[page_no - 1]
        success = 1
        msg = "Records Found"
        total_count = count
    print(data)
    frappe.response["success"] = success
    frappe.response["message"] = msg
    frappe.response["data"] = data
    frappe.response["total_count"] = total_count

@frappe.whitelist(methods=["GET","POST","PUT"])
def get_sfg_dispatch_request_list(user_id,filters=None,page_no=1):
    success,msg,data,totalCount=0,"Failed",[],0
    userId,pageNo,conditions = user_id,page_no,""
    # filters = purchase_invoiceId
    values = {"userId":userId}
    role = ""
    no_role = 0
    if "CC User" in frappe.get_roles(userId):
        role = 'sdr.owner like "{0}" or sdr.owner not like "{0}"'.format(userId)
        # if frappe.db.exists("S4S User details",userId):
        # 	get_usd = frappe.get_doc("S4S User details",userId)
        # 	if get_usd.inward_warehouse:
        # 		role+=' OR pe.set_warehouse="{0}"'.format(get_usd.inward_warehouse)
        # role = "("+role+")"
    # elif "VLCC User" in frappe.get_roles(userId):
    # 	role = 'pe.owner="{0}"'.format(userId)
    # elif "ME Field Executive" in frappe.get_roles(userId):
    # 	pass
    else:
        no_role = 1
    print(role)
    if filters!=None:
        values["filters"] = "%%%s%%"%filters
        conditions += "(sdr.name like %(filters)s) or sdr.dcm_name like %(filters)s"
    # if transactionId!=None:
    # 	values["transactionId"] = "%%%s%%"%transactionId
    # 	conditions += "or pi.s4s_purchase like %(transactionId)s" if conditions!="" else " pi.s4s_purchase like %(transactionId)s"
    # print(conditions)
    if no_role!=1:
        result = frappe.db.sql("""
            SELECT
                sdr.name as sfg_dispatch_request_id,
                sdr.dcm_name as dcm_name,
                sdr.dcm_location as dcm_location
            FROM 
                `tabSFG Dispatch Request` sdr
            WHERE
                {0}
                {1}
            ORDER BY
                sdr.creation DESC
            """.format(role,
                "AND ("+conditions+" )" if conditions!="" else conditions 
            ),
            values,
            as_dict=1
        )
        count = len(result)
        if not count:
            success = 1
            msg = "No Records Found"
        if count !=0:
            total_pages = math.ceil(int(count)/10)
            pageNo = int(pageNo) if int(pageNo)<= total_pages else total_pages
            result = [result[i:i+10] for i in range(0, len(result), 10)]
            success = 1
            msg = "Records Found"
            data = result[int(pageNo)-1]
            totalCount = count
    else:
        success = 1
        msg = "Records Not Found.User does not have any role in CC,VLCC,ME"
    frappe.response["success"] = success
    frappe.response["message"] = msg
    frappe.response["data"] = data
    frappe.response["total_count"] = totalCount

@frappe.whitelist(methods=["GET","POST","PUT"])
def get_inward_vlcc_dispatch_list(user_id,filters=None,page_no=1):
    success,msg,data,totalCount=0,"Failed",[],0
    userId,pageNo,conditions = user_id,page_no,""
    # filters = purchase_invoiceId
    values = {"userId":userId}
    role = ""
    no_role = 0
    if "CC User" in frappe.get_roles(userId):
        role = 'se.owner like "{0}"'.format(userId)
        if frappe.db.exists("User Permission",{"user":userId,"allow":"S4S CC List"}):
            get_usp = frappe.get_all("User Permission",{"user":userId,"allow":"S4S CC List"},["for_value"])
            get_usp = [d['for_value'] for d in get_usp]
            get_usp = "(" + ", ".join(["'" + x + "'" for x in get_usp]) + ")"
            role+= ' OR se.cc_name IN {0}'.format(get_usp)
        role = "("+role+")"
    else:
        no_role = 1
    if filters!=None:
        values["filters"] = "%%%s%%"%filters
        conditions += "(se.name like %(filters)s)"
    if no_role!=1:
        result = frappe.db.sql("""
            SELECT
                se.name as inward_vlcc_dispatch_id,
                se.stock_entry_type as stock_entry_type,
                se.from_warehouse as from_warehouse,
                se.cc_name as cc_name
            FROM 
                `tabStock Entry` se
            WHERE
                {0}
                {1}
            ORDER BY
                se.creation DESC
            """.format(role,
                "AND ("+conditions+" )" if conditions!="" else conditions 
            ),
            values,
            as_dict=1
        )
        count = len(result)
        if not count:
            success = 1
            msg = "No Records Found"
        if count !=0:
            total_pages = math.ceil(int(count)/10)
            pageNo = int(pageNo) if int(pageNo)<= total_pages else total_pages
            result = [result[i:i+10] for i in range(0, len(result), 10)]
            success = 1
            msg = "Records Found"
            data = result[int(pageNo)-1]
            totalCount = count
    else:
        success = 1
        msg = "Records Not Found.User does not have any role in CC,VLCC,ME"
    frappe.response["success"] = success
    frappe.response["message"] = msg
    frappe.response["data"] = data
    frappe.response["total_count"] = totalCount

@frappe.whitelist(methods=["GET","POST","PUT"])
def get_stock_entry_details(stock_entry_id):
    success= 0
    msg = "Record Not Found"
    data=[]
    if stock_entry_id and frappe.db.exists("Stock Entry",stock_entry_id):
        success= 1
        msg = "Record Found"
        # data = frappe.get_doc("Stock Entry",stock_entry_id)
        data = frappe.get_all("Stock Entry",filters={"name":stock_entry_id},fields=['name', 'stock_entry_type', 'purpose', 'add_to_transit', 'company', 'posting_date', 'posting_time', 'set_posting_time', 'inspection_required', 'from_bom', 'apply_putaway_rule', 'is_s4s_purchase', 'material_transfer_wip_to_fg', 'purchase_rate', 'fg_completed_qty', 'use_multi_level_bom', 'from_warehouse','to_warehouse', 'total_outgoing_value', 'total_incoming_value', 'value_difference', 'rm_size', 'foreign_material', 'quality', 'rejected_total_bags', 'rejected_total_goni_weight', 'no_of_bags', 'total_bags', 'total_goni_weight', 'total_additional_costs', 'letter_head', 'is_opening', 'per_transferred', 'total_amount', 'is_return'])[0]
        data["items"]=frappe.get_all("Stock Entry Detail",filters={"parent":stock_entry_id},fields=['s_warehouse', 'item_code', 'item_name', 'is_finished_item', 'is_scrap_item', 'is_process_loss', 'description', 'item_group', 'qty', 'transfer_qty', 'retain_sample', 'uom', 'stock_uom', 'conversion_factor', 'sample_quantity', 'basic_rate', 'additional_cost', 'valuation_rate', 'allow_zero_valuation_rate', 'set_basic_rate_manually', 'basic_amount', 'amount', 'batch_no', 'expense_account', 'cost_center', 'actual_qty', 'transferred_qty', 'allow_alternative_item'])
    frappe.response["success"] = success
    frappe.response["message"] = msg
    frappe.response["stock_entry_details"] = data

@frappe.whitelist(methods=["GET","POST","PUT","PATCH"])
def update_stock_entry(stock_entry_id,params):
    success = 0
    msg = "Failed"
    doc_status = 0
    if not frappe.db.exists("Stock Entry",{"name":stock_entry_id,"docstatus":0}):
        doc_status = 1
        success = 1
        msg = "Stock Entry not in Draft."
    if stock_entry_id and doc_status==0 and params:
        if type(params) != str:
            params = json.dumps(params)
        params = json.loads(params)
        doc = frappe.get_doc("Stock Entry",stock_entry_id)
        doc.update(params)
        doc.save()
        success = 1
        msg = "Stock Entry updated successfully."
    frappe.response["success"]=success
    frappe.response["msg"]=msg

# @frappe.whitelist(methods=["GET","POST","PUT"])
# def update_transaction(transaction_id,status):
# 	success=0
# 	msg = "Failed"
# 	if frappe.db.exists("S4S Purchase",transaction_id):
# 		get_purchase = frappe.get_doc("S4S Purchase",transaction_id)
# 		if status in ["Approved by CC Manager","Rejected by CC Manager"]:
# 			get_purchase.approved_status = status
# 			get_purchase.save()
# 			success=1
# 			msg="Status updated successfully."
# 		else:
# 			success=1
# 			msg="Status not updated"
# 	frappe.response["success"] = success
# 	frappe.response["message"] = msg

@frappe.whitelist(methods=["GET","POST","PUT"])
def submit_transaction(user_id,transaction_id,status=None,purpose=0):
    success=0
    msg="Failed"
    if purpose==1 or purpose=="1":
        print()
        if frappe.db.exists("S4S Purchase",{"name":transaction_id,"docstatus":0}):
            s4s_purchase = frappe.get_doc("S4S Purchase",transaction_id)
            s4s_purchase.save().submit()
            make_purchase_receipt(s4s_purchase,user_id)
            success=1
            msg="Document is submitted successfully."
        else:
            success=1
            msg="Document not in Draft."
    elif purpose==0 or purpose=="0":
        print()
        if frappe.db.exists("S4S Purchase",transaction_id):
            get_purchase = frappe.get_doc("S4S Purchase",transaction_id)
            if status in ["Approved by CC Manager","Rejected by CC Manager"]:
                get_purchase.approved_status = status
                get_purchase.save()
                success=1
                msg="Status updated successfully."
        else:
            success=1
            msg="Status not updated"
    else:
        success=1
        msg="Purpose should be 0 or 1."
    frappe.response["success"]=success
    frappe.response["msg"]=msg

def make_purchase_receipt(s4s_purchase,user):
    doc = frappe.new_doc("Purchase Receipt")
    doc.supplier = s4s_purchase.supplier
    doc.vlcc_name = s4s_purchase.vlcc_name
    doc.cc_name = s4s_purchase.cc_name
    doc.village = s4s_purchase.village
    doc.taluka = s4s_purchase.taluka
    doc.district = s4s_purchase.district
    doc.set_warehouse = s4s_purchase.set_warehouse
    doc.s4s_purchase = s4s_purchase.name
    doc.append("items",{
        "item_code": s4s_purchase.purchase_receipt_details[0].item_code,
        "qty": s4s_purchase.total_weight,
        "variety": s4s_purchase.purchase_receipt_details[0].variety,
        "moisture_content" : s4s_purchase.purchase_receipt_details[0].moisture,
        "rate" : s4s_purchase.total_amount / s4s_purchase.total_weight
    })
    doc.taxes_and_charges = s4s_purchase.supplier_deductions
    # doc.taxes = []
    doc.taxes = s4s_purchase.taxes
    doc.save()
    print("purchase receipt")
    # for pr in doc.taxes:
    # 	print(pr.tax_amount)
    # 	for sp in s4s_purchase.taxes:
    # 		if pr.account_head == sp.account_head:
    # 			pr.tax_amount = sp.tax_amount
    # doc.save()
    doc.submit()
    pi = make_purchase_invoice(doc.name)
    pi.save()
    pi.submit()
    print("done purchase invoice")   
    if frappe.db.exists("S4S User details",user):
        get_user = frappe.get_doc("S4S User details",user)
        if get_user.transit_warehouse:
            se = make_stock_entry(doc.name)
            se.from_warehouse = doc.set_warehouse
            se.to_warehouse = get_user.transit_warehouse
            se.add_to_transit = 1
            se.s4ssupplier = doc.supplier
            se.purchase_rate = s4s_purchase.total_amount / s4s_purchase.total_weight
            se.save()
            # se.submit()

        if frappe.db.get_value("Stock Entry Detail",{'reference_purchase_receipt':doc.name},['parent']):
            se_name = frappe.db.get_value("Stock Entry Detail",{'reference_purchase_receipt':doc.name},['parent'])
            frappe.db.sql(f"""
                update `tabStock Entry` set custom_supplier = '{s4s_purchase.supplier}', custom_supplier_name = '{s4s_purchase.supplier_name}', s4ssupplier = '', me_name = '', is_s4s_purchase = 1
                where name = '{se_name}'
            """)

@frappe.whitelist(methods=["GET","POST","PUT"])
def get_price_list(filters=None,page_no=1):
    success,msg,data,totalCount=0,"Failed",[],0
    pageNo=page_no
    if frappe.db.count("S4S Price List") > 0:
        print()
        if filters!=None:
            result = frappe.get_all("S4S Price List",filters={"name": ["like", f"%{filters}%"]},fields=["name","currency"])
        else:
            result = frappe.get_all("S4S Price List",fields=["name","currency"])
        count = len(result)
        if not count:
            success = 1
            msg = "No Records Found"
        if count !=0:
            total_pages = math.ceil(int(count)/10)
            pageNo = int(pageNo) if int(pageNo)<= total_pages else total_pages
            result = [result[i:i+10] for i in range(0, len(result), 10)]
            success = 1
            msg = "Records Found"
            data = result[int(pageNo)-1]
            totalCount = count
    else:
        success = 1
        msg = "Records Not Found."
    frappe.response["success"] = success
    frappe.response["message"] = msg
    frappe.response["data"] = data
    frappe.response["total_count"] = totalCount

@frappe.whitelist(methods=["GET","POST","PUT"])
def get_price_list_details(price_list_id):
    success=0
    msg = "Failed"
    data={}
    if frappe.db.exists("S4S Price List",price_list_id):
        success= 1
        msg = "Record Found"
        # data = frappe.get_doc("Stock Entry",stock_entry_id)
        # data = frappe.get_doc("S4S Price List",price_list_id,fields=["*"])
        # print(data)
        data = frappe.get_all("S4S Price List",filters={"name":price_list_id},fields=['name', 'date', 'price_list_name', 'currency', 'buying'])[0]
        data["item_price_list"]=frappe.get_all("S4S Item Price",filters={"parent":price_list_id},fields=['item_code', 'item_name', 'uom', 'price_list_rate'])
    frappe.response["success"] = success
    frappe.response["message"] = msg
    frappe.response["price_list_details"] = data

frappe.whitelist(methods=["GET","POST","PUT"])
def submit_price_list(price_list_id):
    success=0
    msg="Failed"
    if frappe.db.exists("S4S Price List",price_list_id):
        print()
        if frappe.db.exists("S4S Price List",{"name":price_list_id,"doctstatus":0}):
            doc = frappe.get_doc("S4S Price List",price_list_id)
            doc.save().submit()
            success=1
            msg="Price list successfully submitted."
        else:
            success=1
            msg="Price list not in Draft."
    else:
        success=1
        msg="Price list does not exists."
    frappe.response["success"] = success
    frappe.response["message"] = msg

@frappe.whitelist(methods=["GET","POST","PUT"])
def add_price_list(params):
    success=0
    msg="Failed"
    if params:
        if type(params) != str:
            params = json.dumps(params)
        params = json.loads(params)
        doc = frappe.new_doc("S4S Price List")
        doc.update(params)
        doc.price_list_name = doc.date
        # doc.meta.bypass_doctype_permission = True
        doc.save()
        success=1
        msg="Price List added successfully."
    frappe.response["success"] = success
    frappe.response["message"] = msg

@frappe.whitelist(methods=["GET","POST","PUT","PATCH"])
def update_price_list(price_list_id,params=None,purpose=0):
    success = 0
    msg = "Failed"
    doc_status = 0
    if not frappe.db.exists("S4S Price List",{"name":price_list_id,"docstatus":0}):
        doc_status = 1
        success = 1
        msg = "Price List not in draft."
    if price_list_id and doc_status==0 and params:
        if type(params) != str:
            params = json.dumps(params)
        params = json.loads(params)
        doc = frappe.get_doc("S4S Price List",price_list_id)
        if purpose==0 or purpose=="0":
            doc.update(params)
            doc.save()
        if purpose==1 or purpose=="1":
            doc.update(params)
            doc.save().submit()
        success = 1
        msg = "Price List updated successfully."
    frappe.response["success"]=success
    frappe.response["msg"]=msg

@frappe.whitelist(methods=["GET","POST","PUT"])
def get_sfg_dispatch_request_details(sfg_dispatch_req_id):
    success=0
    msg = "Failed"
    data=[]
    if frappe.db.exists("SFG Dispatch Request",sfg_dispatch_req_id):
        success= 1
        msg = "Record Found"
        # data = frappe.get_doc("SFG Dispatch Request",sfg_dispatch_req_id)
        data = frappe.get_all("SFG Dispatch Request",filters={"name":sfg_dispatch_req_id},fields=['name', 'dcm_name', 'dcm_location', 'approval_status', 'dcm_supervisor', 'cc_user', 'factory_rm_store_manager', 'logistic_supervisor', 'date', 'pickup_date', 'dcm_warehouse', 'cc_warehouse', 'trip_start', 'trip_end', 'vehicle_no', 'vehicle_model', 'driver_name', 'assigned_vehicle', 'scheduling_date'])[0]
        data["dcm_dispatch_item"]=frappe.get_all("DCM Dispatch Item",filters={"parent":sfg_dispatch_req_id},fields=['item_name', 'qty', 'uom', 'no_of_bags', 'batch_no', 'bag_condition', 'colour'])
    frappe.response["success"] = success
    frappe.response["message"] = msg
    frappe.response["sfg_dispatch_request_details"] =data

@frappe.whitelist(methods=["GET","POST","PUT","PATCH"])
def update_sfg_dispatch_request(sfg_dispatch_request_id,params=None,purpose=0):
    success = 0
    msg = "Failed"
    doc_status = 0
    if not frappe.db.exists("SFG Dispatch Request",{"name":sfg_dispatch_request_id,"docstatus":0}):
        doc_status = 1
        success = 1
        msg = "SFG Dispatch Request not in draft."
    if sfg_dispatch_request_id and doc_status==0 and params:
        if type(params) != str:
            params = json.dumps(params)
        params = json.loads(params)
        doc = frappe.get_doc("SFG Dispatch Request",sfg_dispatch_request_id)
        if purpose==0 or purpose=="0":
            doc.update(params)
            doc.save()
        if purpose==1 or purpose=="1":
            doc.update(params)
            doc.save().submit()
        success = 1
        msg = "SFG Dispatch Request updated successfully."
    frappe.response["success"]=success
    frappe.response["msg"]=msg

@frappe.whitelist(methods=["GET","POST","PUT"])
def get_payment_entry_details(payment_entry_id):
    success=0
    msg = "Failed"
    data=[]
    if frappe.db.exists("Payment Entry",payment_entry_id):
        success= 1
        msg = "Record Found"
        # data = frappe.get_doc("Payment Entry",payment_entry_id)
        data = frappe.get_all("Payment Entry",filters={"name":payment_entry_id},fields=['payment_type', 'payment_order_status', 'posting_date', 'company', 'mode_of_payment', 'party_type', 'party', 'party_name', 'contact_person', 'contact_email', 'party_balance', 'paid_from', 'paid_from_account_type', 'paid_from_account_currency', 'paid_from_account_balance', 'paid_to', 'paid_to_account_type', 'paid_to_account_currency', 'paid_to_account_balance', 'paid_amount', 'paid_amount_after_tax', 'source_exchange_rate', 'base_paid_amount', 'base_paid_amount_after_tax', 'received_amount', 'received_amount_after_tax', 'target_exchange_rate', 'base_received_amount', 'base_received_amount_after_tax', 'total_allocated_amount', 'base_total_allocated_amount', 'unallocated_amount', 'difference_amount', 'apply_tax_withholding_amount', 'base_total_taxes_and_charges', 'total_taxes_and_charges', 'reference_no', 'reference_date', 'status', 'custom_remarks', 'remarks',  'title',"vlcc_name","cc_name","village","taluka","district","s4s_purchase"])[0]
        data["references"]=frappe.get_all("Payment Entry Reference",filters={"parent":payment_entry_id},fields=['reference_doctype', 'reference_name', 'due_date', 'total_amount', 'outstanding_amount', 'allocated_amount', 'exchange_rate', 'exchange_gain_loss'])
    frappe.response["success"] = success
    frappe.response["message"] = msg
    frappe.response["payment_entry_details"] =data

@frappe.whitelist(methods=["GET","POST","PUT","PATCH"])
def update_payment_entry(payment_entry_id,params=None,purpose=0):
    success = 0
    msg = "Failed"
    doc_status = 0
    if not frappe.db.exists("Payment Entry",{"name":payment_entry_id,"docstatus":0}):
        doc_status = 1
        success = 1
        msg = "Payment Entry not in draft."
    if payment_entry_id and doc_status==0 and params:
        if type(params) != str:
            params = json.dumps(params)
        params = json.loads(params)
        doc = frappe.get_doc("Payment Entry",payment_entry_id)
        if purpose==0 or purpose=="0":
            doc.update(params)
            doc.save()
        if purpose==1 or purpose=="1":
            doc.update(params)
            doc.save().submit()
        success = 1
        msg = "Payment Entry updated successfully."
    frappe.response["success"]=success
    frappe.response["msg"]=msg

@frappe.whitelist(methods=["GET","POST","PUT"])
def get_purchase_receipt_details(purchase_receipt_id):
    success=0
    msg = "Failed"
    data=[]
    if frappe.db.exists("Purchase Receipt",purchase_receipt_id):
        success= 1
        msg = "Record Found"
        # data = frappe.get_doc("Purchase Receipt",purchase_receipt_id)
        data = frappe.get_all("Purchase Receipt",filters={"name":purchase_receipt_id},fields=['name', 'supplier', 'supplier_name', 'supplier_type', 'company', 'posting_date', 'posting_time', 'set_posting_time', 'apply_putaway_rule', 'is_return', 'supplier_address', 'contact_person', 'address_display', 'contact_display', 'contact_mobile', 'contact_email', 'shipping_address', 'place_of_supply', 'shipping_address_display', 'company_gstin', 'billing_address', 'billing_address_display', 'currency', 'conversion_rate', 'buying_price_list', 'price_list_currency', 'plc_conversion_rate', 'ignore_pricing_rule', 'set_warehouse', 'is_subcontracted', 'total_qty', 'base_total', 'base_net_total', 'total_net_weight', 'total', 'net_total', 'tax_category', 'taxes_and_charges', 'base_taxes_and_charges_added', 'base_taxes_and_charges_deducted', 'base_total_taxes_and_charges', 'taxes_and_charges_added', 'taxes_and_charges_deducted', 'total_taxes_and_charges', 'apply_discount_on', 'base_discount_amount', 'additional_discount_percentage', 'discount_amount', 'base_grand_total', 'base_rounding_adjustment', 'base_in_words', 'base_rounded_total', 'grand_total', 'rounding_adjustment', 'rounded_total', 'in_words', 'disable_rounded_total', 'status', 'per_billed', 'per_returned', 'is_internal_supplier', 'represents_company', 'letter_head', 'language', 'group_same_items', 's4s_purchase'])[0]
        data["items"]=frappe.get_all("Purchase Receipt Item",filters={"parent":purchase_receipt_id},fields=['item_code', 'item_name', 'description', 'is_nil_exempt', 'is_non_gst', 'item_group', 'image', 'received_qty', 'qty', 'rejected_qty', 'variety', 'moisture_content', 'uom', 'stock_uom', 'conversion_factor', 'retain_sample', 'sample_quantity', 'received_stock_qty', 'stock_qty', 'returned_qty', 'price_list_rate', 'base_price_list_rate', 'margin_type', 'margin_rate_or_amount', 'rate_with_margin', 'discount_percentage', 'discount_amount', 'base_rate_with_margin', 'rate', 'amount', 'base_rate', 'base_amount', 'stock_uom_rate', 'is_free_item', 'net_rate', 'net_amount', 'base_net_rate', 'base_net_amount', 'valuation_rate', 'item_tax_amount', 'rm_supp_cost', 'landed_cost_voucher_amount', 'billed_amt', 'warehouse', 'is_fixed_asset', 'allow_zero_valuation_rate', 'serial_no', 'include_exploded_items', 'batch_no', 'item_tax_rate', 'weight_per_unit', 'total_weight', 'weight_uom', 'expense_account', 'cost_center'])
        data["taxes"]=frappe.get_all("Purchase Taxes and Charges",filters={"parent":purchase_receipt_id},fields=['category', 'add_deduct_tax', 'charge_type', 'included_in_print_rate', 'included_in_paid_amount', 'account_head', 'description', 'rate', 'cost_center', 'account_currency', 'tax_amount', 'tax_amount_after_discount_amount', 'total', 'base_tax_amount', 'base_total', 'base_tax_amount_after_discount_amount', 'item_wise_tax_detail'])
    frappe.response["success"] = success
    frappe.response["message"] = msg
    frappe.response["purchase_receipt_details"] =data

@frappe.whitelist(methods=["GET","POST","PUT"])
def get_purchase_invoice_details(purchase_invoice_id):
    success=0
    msg = "Failed"
    data=[]
    if frappe.db.exists("Purchase Invoice",purchase_invoice_id):
        success= 1
        msg = "Record Found"
        # data = frappe.get_doc("Purchase Invoice",purchase_invoice_id)
        data = frappe.get_all("Purchase Invoice",filters={"name":purchase_invoice_id},fields=['name', 'supplier', 'supplier_name', 'due_date', 'company', 'posting_date', 'posting_time', 'set_posting_time', 'is_paid', 'is_return', 'apply_tds', 'supplier_address', 'address_display', 'contact_person', 'contact_display', 'contact_mobile', 'contact_email', 'shipping_address', 'place_of_supply', 'shipping_address_display', 'company_gstin', 'billing_address', 'billing_address_display', 'currency', 'conversion_rate', 'buying_price_list', 'price_list_currency', 'plc_conversion_rate', 'ignore_pricing_rule', 'set_warehouse', 'is_subcontracted', 'update_stock', 'total_qty', 'base_total', 'base_net_total', 'total_net_weight', 'total', 'net_total', 'tax_category', 'taxes_and_charges', 'base_taxes_and_charges_added', 'base_taxes_and_charges_deducted', 'base_total_taxes_and_charges', 'taxes_and_charges_added', 'taxes_and_charges_deducted', 'total_taxes_and_charges', 'apply_discount_on', 'base_discount_amount', 'additional_discount_percentage', 'discount_amount', 'base_grand_total', 'base_rounding_adjustment', 'base_rounded_total', 'base_in_words', 'grand_total', 'rounding_adjustment', 'rounded_total', 'in_words', 'total_advance', 'outstanding_amount', 'disable_rounded_total', 'paid_amount', 'base_paid_amount', 'write_off_amount', 'base_write_off_amount', 'allocate_advances_automatically', 'ignore_default_payment_terms_template', 'letter_head', 'group_same_items', 'language', 'gst_category', 'on_hold', 'status', 'represents_company', 'is_internal_supplier', 'credit_to', 'party_account_currency', 'is_opening', 'against_expense_account', 'remarks', 'per_received', 'eligibility_for_itc', 'export_type', 'invoice_copy', 'itc_central_tax', 'itc_cess_amount', 'itc_integrated_tax', 'itc_state_tax', 'reason_for_issuing_document', 'reverse_charge', 's4s_purchase'])[0]
        data["items"]=frappe.get_all("Purchase Invoice Item",filters={"parent":purchase_invoice_id},fields=['item_code', 'item_name', 'description', 'is_nil_exempt', 'is_non_gst', 'item_group', 'image', 'received_qty', 'qty', 'rejected_qty', 'uom', 'conversion_factor', 'stock_uom', 'stock_qty', 'price_list_rate', 'base_price_list_rate', 'margin_type', 'margin_rate_or_amount', 'rate_with_margin', 'discount_percentage', 'discount_amount', 'base_rate_with_margin', 'rate', 'amount', 'base_rate', 'base_amount', 'stock_uom_rate', 'is_free_item', 'net_rate', 'net_amount', 'base_net_rate', 'base_net_amount', 'taxable_value', 'valuation_rate', 'item_tax_amount', 'landed_cost_voucher_amount', 'rm_supp_cost', 'warehouse', 'expense_account', 'is_fixed_asset', 'enable_deferred_expense', 'allow_zero_valuation_rate', 'item_tax_rate', 'include_exploded_items', 'purchase_receipt', 'pr_detail', 'weight_per_unit', 'total_weight', 'weight_uom', 'cost_center'])
        data["taxes"]=frappe.get_all("Purchase Taxes and Charges",filters={"parent":purchase_invoice_id},fields=['category', 'add_deduct_tax', 'charge_type', 'included_in_print_rate', 'included_in_paid_amount', 'account_head', 'description', 'rate', 'cost_center', 'account_currency', 'tax_amount', 'tax_amount_after_discount_amount', 'total', 'base_tax_amount', 'base_total', 'base_tax_amount_after_discount_amount', 'item_wise_tax_detail'])
        data["payment_schedule"]=frappe.get_all("Payment Schedule",filters={"parent":purchase_invoice_id},fields=['due_date', 'invoice_portion', 'discount_type', 'discount', 'payment_amount', 'outstanding', 'paid_amount', 'discounted_amount', 'base_payment_amount'])
    frappe.response["success"] = success
    frappe.response["message"] = msg
    frappe.response["purchase_invoice_details"] =data


@frappe.whitelist(methods=["GET", "POST", "PUT"])
def get_dcm_material_request_list(filters=None, page_no=1):
    document_type = "DCM Material Request"
    fields = ["name as dcm_material_request_id", "dcm_name", "dcm_location"]
    condition = None
    success, msg, data, total_count = 0, "Failed", [], 0

    if filters:
        condition = [
            f"(`tab{document_type}`.`name` like '%{filters}%') or (`tab{document_type}`.`dcm_name` like '%{filters}%')"
        ]

    result = get_all(doctype=document_type, filters=condition, fields=fields,order_by="creation desc")
    count = len(result)

    if count == 0:
        success = 1
        msg = "No Records Found"
    else:
        total_pages = math.ceil(count / 10)
        page_no = min(int(page_no), total_pages)
        paginated_result = [result[i:i + 10] for i in range(0, count, 10)]
        data = paginated_result[page_no - 1]
        success = 1
        msg = "Records Found"
        total_count = count
    frappe.response["success"] = success
    frappe.response["message"] = msg
    frappe.response["data"] = data
    frappe.response["total_count"] = total_count


@frappe.whitelist(methods=["GET","POST","PUT"])
def get_dcm_material_request_details(dcm_material_request_id):
    success= 0
    msg = "Record Not Found"
    data=[]
    if dcm_material_request_id and frappe.db.exists("DCM Material Request",dcm_material_request_id):
        success= 1
        msg = "Record Found"
        data = frappe.get_all("DCM Material Request",filters={"name":dcm_material_request_id},fields=['name','dcm_name', 'request_type', 'request_date', 'delivery_date', 'purpose', 'rm_warehouse', 'dcm_warehouse',  'material_request', 'dcm_location', 'approval_status', 'trip_start', 'trip_end', 'vehicle_no', 'vehicle_model', 'driver_name', 'driver_mobile_number', 'assigned_vehicle', 'scheduling_date', 'dcm_supervisor', 'cc_user', 'logistic_supervisor', 's4s_logistic_manager'])[0]
        data["items"]=frappe.get_all("S4S DCM Material request",filters={"parent":dcm_material_request_id},fields=['item_code', 'item_name', 'qty','uom', 'approved_qty', 'cc_approved_qty','no_of_bags'])
    frappe.response["success"] = success
    frappe.response["message"] = msg
    frappe.response["dcm_material_req_details"] = data

@frappe.whitelist(methods=["GET","POST","PUT","PATCH"])
def update_dcm_material_request(dcm_material_request_id,params=None,purpose=0):
    success = 0
    msg = "Failed"
    doc_status = 0
    if not frappe.db.exists("DCM Material Request",{"name":dcm_material_request_id,"docstatus":0}):
        doc_status = 1
        success = 1
        msg = "DCM Material Request not in draft."
    if dcm_material_request_id and doc_status==0 and params:
        if type(params) != str:
            params = json.dumps(params)
        params = json.loads(params)
        doc = frappe.get_doc("DCM Material Request",dcm_material_request_id)
        if purpose==0 or purpose=="0":
            doc.update(params)
            doc.save()
        if purpose==1 or purpose=="1":
            doc.update(params)
            doc.save().submit()
        success = 1
        msg = "DCM Material Request updated successfully."
    frappe.response["success"]=success
    frappe.response["msg"]=msg

@frappe.whitelist(methods=["GET","POST","PUT"])
def get_dcm_list():
    dcm_list = frappe.get_all("DCM List")
    frappe.response["success"] = 1
    frappe.response["message"] = "Found"
    frappe.response["data"] = dcm_list

@frappe.whitelist(methods=["GET","POST","PUT"])
def get_dcm_material_request_form_data(dcm_id=None):
    success=0
    msg="Not Found"
    dcm_location=""
    dcm_warehouse=""
    warehouse_list = frappe.get_all("Warehouse")
    if dcm_id and frappe.db.exists("DCM List",dcm_id):
        get_doc=frappe.get_doc("DCM List",dcm_id)
        dcm_location = get_doc.location
        dcm_warehouse=get_doc.transit_location
        success=1
        msg="Found"
    frappe.response["success"] = success
    frappe.response["message"] = msg
    frappe.response["dcm_location"] = dcm_location
    frappe.response["dcm_warehouse"] = dcm_warehouse

@frappe.whitelist(methods=["GET","POST","PUT"])
def add_dcm_material_request(params):
    success = 0
    msg = "Failed"
    try:
        if type(params) != str:
            params = json.dumps(params)
        params = json.loads(params)
        params["doctype"] = "DCM Material Request"
        new_doc = frappe.get_doc(params)
        new_doc.save()
        if new_doc:
            success = 1
            msg = "DCM Material Request added successfully"
        # return new_doc
    
    except HTTPError as http_err:
        print(f'HTTP error occurred: {http_err}')
    except Exception as err:
        print(f'Other error occurred: {err}')
    
    frappe.response['success']=success
    frappe.response['message']=msg

@frappe.whitelist(methods=["GET","POST","PUT"])
def get_vehicle_list():
    vehicle_list = frappe.get_all("S4S Vehicle")
    frappe.response["success"] = 1
    frappe.response["message"] = "Found"
    frappe.response["vehicle_list"] = vehicle_list

@frappe.whitelist(methods=["GET","POST","PUT"])
def get_vehicle_details(vehicle_id):
    success=0
    msg="Not Found"
    vehicle_details=[]
    if vehicle_id and frappe.db.exists("S4S Vehicle",vehicle_id):
        vehicle_details=frappe.get_doc("S4S Vehicle",vehicle_id,["name","vehicle_model","driver_name","driver_mobile_number"])
        success=1
        msg="Found"
    frappe.response["success"] = success
    frappe.response["message"] = msg
    frappe.response["vehicle_details"] = vehicle_details

@frappe.whitelist(methods=["GET","POST","PUT"])
def get_customer_list(user_id,filters=None,page_no=1):
    document_type = "Customer"
    fields = ["name as customer_id","customer_name as customer_name","customer_group as customer_group"]
    condition = None
    success, msg, data, total_count = 0, "Failed", [], 0
    # permitted_doctypes = get_user_permissions(user_id)
    # print(permitted_doctypes,type(permitted_doctypes["S4S CC List"][0]))
    # get_per_doc = get_allowed_docs_for_doctype(permitted_doctypes["S4S CC List"],document_type)
    # print(get_per_doc)
    # if document_type not in permitted_doctypes:
    #     frappe.throw("Access denied for the specified doctype.")

    if filters:
        condition = [
            f"(`tab{document_type}`.`name` like '%{filters}%') or (`tab{document_type}`.`customer` like '%{filters}%')"
        ]
    print(frappe.get_list(document_type))
    result = get_all(doctype=document_type, filters=condition, fields=fields,order_by="creation desc")
    count = len(result)

    if count == 0:
        success = 1
        msg = "No Records Found"
    else:
        total_pages = math.ceil(count / 10)
        page_no = min(int(page_no), total_pages)
        paginated_result = [result[i:i + 10] for i in range(0, count, 10)]
        data = paginated_result[page_no - 1]
        success = 1
        msg = "Records Found"
        total_count = count
    print(data)
    frappe.response["success"] = success
    frappe.response["message"] = msg
    frappe.response["data"] = data
    frappe.response["total_count"] = total_count

@frappe.whitelist(methods=["GET","POST","PUT"])
def get_customer_details(customer_id):
    success=0
    msg="Not Found"
    customer_details=[]
    if customer_id and frappe.db.exists("Customer",customer_id):
        # data = frappe.get_doc("Customer",customer_id)
        # print(data.as_dict())
        customer_details=frappe.get_all("Customer",filters={"name":customer_id},fields=["name","salutation","customer_name","company","abbr","gender","customer_type","gst_category","export_type","pan","tax_withholding_category","default_bank_account","lead_name","opportunity_name","image","account_manager","customer_group","territory","tax_id","tax_category","so_required","dn_required","disabled","is_internal_customer","represents_company","default_currency","default_price_list","website","customer_primary_contact","mobile_no","email_id","customer_primary_address","primary_address","payment_terms","customer_details","market_segment","industry","language","loyalty_program","loyalty_program_tier","default_sales_partner","default_commission_rate","customer_pos_id"])
        success=1
        msg="Found"
    frappe.response["success"] = success
    frappe.response["message"] = msg
    frappe.response["customer_details"] = customer_details

@frappe.whitelist(methods=["GET","POST","PUT"])
def get_sales_order_list(user_id,filters=None,page_no=1):
    document_type = "Sales Order"
    fields = ["name as sales_order_id","customer as customer_id","customer_name as customer_name","delivery_date as delivery_date"]
    condition = None
    success, msg, data, total_count = 0, "Failed", [], 0
    # permitted_doctypes = get_user_permissions(user_id)
    # print(permitted_doctypes,type(permitted_doctypes["S4S CC List"][0]))
    # get_per_doc = get_allowed_docs_for_doctype(permitted_doctypes["S4S CC List"],document_type)
    # print(get_per_doc)
    # if document_type not in permitted_doctypes:
    #     frappe.throw("Access denied for the specified doctype.")

    if filters:
        condition = [
            f"(`tab{document_type}`.`name` like '%{filters}%') or (`tab{document_type}`.`customer` like '%{filters}%')"
        ]
    print(frappe.get_list(document_type))
    result = get_all(doctype=document_type, filters=condition, fields=fields,order_by="creation desc")
    count = len(result)

    if count == 0:
        success = 1
        msg = "No Records Found"
    else:
        total_pages = math.ceil(count / 10)
        page_no = min(int(page_no), total_pages)
        paginated_result = [result[i:i + 10] for i in range(0, count, 10)]
        data = paginated_result[page_no - 1]
        success = 1
        msg = "Records Found"
        total_count = count
    print(data)
    frappe.response["success"] = success
    frappe.response["message"] = msg
    frappe.response["data"] = data
    frappe.response["total_count"] = total_count

@frappe.whitelist(methods=["GET","POST","PUT"])
def get_sales_order_details(sales_order_id):
    success= 0
    msg = "Record Not Found"
    data=[]
    if sales_order_id and frappe.db.exists("Sales Order",sales_order_id):
        success= 1
        msg = "Record Found"
        # data = frappe.get_doc("Sales Order",sales_order_id)
        # print(data.as_dict())
        data = frappe.get_all("Sales Order",filters={"name":sales_order_id},fields=["name","customer","customer_name","type_of_customer","company","transaction_date","delivery_date","po_no","po_date","zoho_so_no","zoho_so_date","transporter_name","driver_name","eway_bill_no","vehicle_no","lr_no","lr_date","customer_address","billing_address_gstin","address_display","contact_person","contact_display","contact_phone","contact_mobile","contact_email","company_address","company_gstin","company_address_display","shipping_address_name","customer_gstin","place_of_supply","shipping_address","dispatch_address_name","dispatch_address","customer_group","territory","selling_price_list","price_list_currency","plc_conversion_rate","set_warehouse","total_qty","base_total","base_net_total","total_net_weight","total","net_total","tax_category","shipping_rule","taxes_and_charges","other_charges_calculation","base_total_taxes_and_charges","total_taxes_and_charges","apply_discount_on","base_discount_amount","additional_discount_percentage","discount_amount","base_grand_total","base_rounding_adjustment","base_rounded_total","base_in_words","grand_total","rounding_adjustment","rounded_total","in_words","advance_paid","disable_rounded_total","payment_terms_template","tc_name","status","amount_eligible_for_commission","commission_rate","total_commission"])[0]
        data["items"]=frappe.get_all("Sales Order Item",filters={"parent":sales_order_id},fields=["item_code","delivery_date","item_name","description","item_group","qty","stock_uom","uom","stock_qty","rate","amount","total_weight","weight_uom","warehouse","target_warehouse","bom_no","projected_qty","actual_qty","ordered_qty","planned_qty","work_order_qty","produced_qty","delivered_qty","returned_qty","transaction_date"])
    frappe.response["success"] = success
    frappe.response["message"] = msg
    frappe.response["sales_order_details"] = data

@frappe.whitelist(methods=["GET","POST","PUT"])
def get_pick_list(user_id,filters=None,page_no=1):
    document_type = "Pick List"
    fields = ["name as pick_list_id","customer as customer_id","customer_name as customer_name","pick_list_date as pick_list_date"]
    condition = None
    success, msg, data, total_count = 0, "Failed", [], 0
    # permitted_doctypes = get_user_permissions(user_id)
    # print(permitted_doctypes,type(permitted_doctypes["S4S CC List"][0]))
    # get_per_doc = get_allowed_docs_for_doctype(permitted_doctypes["S4S CC List"],document_type)
    # print(get_per_doc)
    # if document_type not in permitted_doctypes:
    #     frappe.throw("Access denied for the specified doctype.")

    if filters:
        condition = [
            f"(`tab{document_type}`.`name` like '%{filters}%') or (`tab{document_type}`.`customer` like '%{filters}%')"
        ]
    print(frappe.get_list(document_type))
    result = get_all(doctype=document_type, filters=condition, fields=fields,order_by="creation desc")
    count = len(result)

    if count == 0:
        success = 1
        msg = "No Records Found"
    else:
        total_pages = math.ceil(count / 10)
        page_no = min(int(page_no), total_pages)
        paginated_result = [result[i:i + 10] for i in range(0, count, 10)]
        data = paginated_result[page_no - 1]
        success = 1
        msg = "Records Found"
        total_count = count
    print(data)
    frappe.response["success"] = success
    frappe.response["message"] = msg
    frappe.response["data"] = data
    frappe.response["total_count"] = total_count

@frappe.whitelist(methods=["GET","POST","PUT"])
def get_pick_list_details(pick_list_id):
    success= 0
    msg = "Record Not Found"
    data=[]
    if pick_list_id and frappe.db.exists("Pick List",pick_list_id):
        success= 1
        msg = "Record Found"
        # data = frappe.get_doc("Pick List",pick_list_id)
        # print(data.as_dict())
        data = frappe.get_all("Pick List",filters={"name":pick_list_id},fields=["name","company","abbr","purpose","customer","customer_name","work_order","material_request","for_qty","pick_list_date","cc_name","parent_warehouse","sales_order"])[0]
        data["items"]=frappe.get_all("Pick List Item",filters={"parent":pick_list_id},fields=["item_code","item_name","description","item_group","warehouse","qty","stock_qty","picked_qty","rate","uom","conversion_factor","stock_uom","serial_no","batch_no","sales_order","sales_order_item","product_bundle_item","material_request","material_request_item"])
    frappe.response["success"] = success
    frappe.response["message"] = msg
    frappe.response["pick_list_details"] = data

@frappe.whitelist(methods=["GET","POST","PUT"])
def get_delivery_note_list(user_id,filters=None,page_no=1):
    document_type = "Delivery Note"
    fields = ["name as delivery_note_id","customer as customer_id","customer_name as customer_name","posting_date as delivery_note_date"]
    condition = None
    success, msg, data, total_count = 0, "Failed", [], 0
    # permitted_doctypes = get_user_permissions(user_id)
    # print(permitted_doctypes,type(permitted_doctypes["S4S CC List"][0]))
    # get_per_doc = get_allowed_docs_for_doctype(permitted_doctypes["S4S CC List"],document_type)
    # print(get_per_doc)
    # if document_type not in permitted_doctypes:
    #     frappe.throw("Access denied for the specified doctype.")

    if filters:
        condition = [
            f"(`tab{document_type}`.`name` like '%{filters}%') or (`tab{document_type}`.`customer` like '%{filters}%')"
        ]
    print(frappe.get_list(document_type))
    result = get_all(doctype=document_type, filters=condition, fields=fields,order_by="creation desc")
    count = len(result)

    if count == 0:
        success = 1
        msg = "No Records Found"
    else:
        total_pages = math.ceil(count / 10)
        page_no = min(int(page_no), total_pages)
        paginated_result = [result[i:i + 10] for i in range(0, count, 10)]
        data = paginated_result[page_no - 1]
        success = 1
        msg = "Records Found"
        total_count = count
    print(data)
    frappe.response["success"] = success
    frappe.response["message"] = msg
    frappe.response["data"] = data
    frappe.response["total_count"] = total_count

@frappe.whitelist(methods=["GET","POST","PUT"])
def get_delivery_note_details(delivery_note_id):
    success= 0
    msg = "Record Not Found"
    data=[]
    if delivery_note_id and frappe.db.exists("Delivery Note",delivery_note_id):
        success= 1
        msg = "Record Found"
        # data = frappe.get_doc("Delivery Note",delivery_note_id)
        # print(data.as_dict())
        data = frappe.get_all("Delivery Note",filters={"name":delivery_note_id},fields=["name","customer","customer_name","proforma_invoice","company","abbr","posting_date","posting_time","po_no","po_date","zoho_si_no","zoho_si_date","pick_list","sales_order","shipping_address_name","customer_gstin","place_of_supply","shipping_address","dispatch_address_name","dispatch_address","contact_person","contact_display","contact_mobile","contact_email","customer_address","billing_address_gstin","address_display","company_address","company_gstin","company_address_display","currency","conversion_rate","selling_price_list","price_list_currency","plc_conversion_rate","set_warehouse","set_target_warehouse","scan_barcode","total_qty","base_total","base_net_total","total_net_weight","total","net_total","taxes_and_charges","other_charges_calculation","base_total_taxes_and_charges","total_taxes_and_charges","apply_discount_on","base_discount_amount","additional_discount_percentage","discount_amount","base_grand_total","base_rounding_adjustment","base_rounded_total","base_in_words","grand_total","rounding_adjustment","rounded_total","in_words","transporter","gst_transporter_id","driver","lr_no","vehicle_no","distance","transporter_name","mode_of_transport","driver_name","lr_date","gst_vehicle_type","gst_category","inter_company_reference","per_billed","customer_group","territory","status"])[0]
        data["items"]=frappe.get_all("Delivery Note Item",filters={"parent":delivery_note_id},fields=["item_code","item_name","description","item_group","image","qty","uom","stock_qty","returned_qty","rate","amount","warehouse","target_warehouse","against_sales_order","so_detail","against_sales_invoice","si_detail","dn_detail","pick_list_item","batch_no","serial_no","actual_batch_qty","actual_qty"])
    frappe.response["success"] = success
    frappe.response["message"] = msg
    frappe.response["delivery_note_details"] = data

@frappe.whitelist(methods=["GET","POST","PUT"])
def get_proforma_invoice_list(user_id,filters=None,page_no=1):
    document_type = "Proforma Invoice"
    fields = ["name as proforma_invoice_id","customer as customer_id","customer_name as customer_name","posting_date as delivery_note_date"]
    condition = None
    success, msg, data, total_count = 0, "Failed", [], 0
    # permitted_doctypes = get_user_permissions(user_id)
    # print(permitted_doctypes,type(permitted_doctypes["S4S CC List"][0]))
    # get_per_doc = get_allowed_docs_for_doctype(permitted_doctypes["S4S CC List"],document_type)
    # print(get_per_doc)
    # if document_type not in permitted_doctypes:
    #     frappe.throw("Access denied for the specified doctype.")

    if filters:
        condition = [
            f"(`tab{document_type}`.`name` like '%{filters}%') or (`tab{document_type}`.`customer` like '%{filters}%')"
        ]
    print(frappe.get_list(document_type))
    result = get_all(doctype=document_type, filters=condition, fields=fields,order_by="creation desc")
    count = len(result)

    if count == 0:
        success = 1
        msg = "No Records Found"
    else:
        total_pages = math.ceil(count / 10)
        page_no = min(int(page_no), total_pages)
        paginated_result = [result[i:i + 10] for i in range(0, count, 10)]
        data = paginated_result[page_no - 1]
        success = 1
        msg = "Records Found"
        total_count = count
    print(data)
    frappe.response["success"] = success
    frappe.response["message"] = msg
    frappe.response["data"] = data
    frappe.response["total_count"] = total_count

@frappe.whitelist(methods=["GET","POST","PUT"])
def get_proforma_invoice_details(proforma_invoice_id):
    success= 0
    msg = "Record Not Found"
    data=[]
    if proforma_invoice_id and frappe.db.exists("Proforma Invoice",proforma_invoice_id):
        success= 1
        msg = "Record Found"
        # data = frappe.get_doc("Proforma Invoice",proforma_invoice_id)
        # print(data.as_dict())
        data = frappe.get_all("Proforma Invoice",filters={"name":proforma_invoice_id},fields=["name","customer","customer_name","tax_id","company","posting_date","posting_time","set_posting_time","due_date","po_no","po_date","customer_address","address_display","contact_person","contact_display","contact_mobile","contact_email","territory","shipping_address_name","shipping_address","company_address","company_address_display","dispatch_address_name","currency","conversion_rate","selling_price_list","price_list_currency","set_warehouse","set_target_warehouse","total_billing_amount","total_billing_hours","total_qty","base_total","base_net_total","total_net_weight","total","net_total","taxes_and_charges","shipping_rule","tax_category","other_charges_calculation","base_total_taxes_and_charges","total_taxes_and_charges","base_grand_total","base_rounding_adjustment","base_rounded_total","grand_total","rounding_adjustment","rounded_total","in_words","total_advance","outstanding_amount","disable_rounded_total","cash_bank_account","base_paid_amount","paid_amount","base_change_amount","change_amount","terms","delivery_note","sales_order","status","customer_group","debit_to","party_account_currency"])[0]
        data["items"]=frappe.get_all("Proforma Invoice Item",filters={"parent":proforma_invoice_id},fields=["item_code","item_name","customer_item_code","description","item_group","brand","image","qty","stock_uom","uom","conversion_factor","stock_qty","price_list_rate","base_price_list_rate","margin_type","margin_rate_or_amount","rate","amount","base_rate","base_amount","net_rate","net_amount","base_net_rate","base_net_amount","income_account","expense_account","weight_per_unit","total_weight","weight_uom","warehouse","batch_no","serial_no","sales_order","so_detail","sales_invoice_item","delivery_note","dn_detail","delivered_qty","cost_center"])
        data["payment_schedule"] = frappe.get_all("Payment Schedule",filters={"parent":proforma_invoice_id},fields=["payment_term","description","due_date","mode_of_payment","invoice_portion","discount_type","discount_date","discount","payment_amount","outstanding","paid_amount","discounted_amount","base_payment_amount"])
    frappe.response["success"] = success
    frappe.response["message"] = msg
    frappe.response["proforma_invoice_details"] = data

@frappe.whitelist(methods=["GET","POST","PUT"])
def get_sales_invoice_list(user_id,filters=None,page_no=1):
    document_type = "Sales Invoice"
    fields = ["name as sales_invoice_id","customer as customer_id","customer_name as customer_name","posting_date as delivery_mote_date"]
    condition = None
    success, msg, data, total_count = 0, "Failed", [], 0
    # permitted_doctypes = get_user_permissions(user_id)
    # print(permitted_doctypes,type(permitted_doctypes["S4S CC List"][0]))
    # get_per_doc = get_allowed_docs_for_doctype(permitted_doctypes["S4S CC List"],document_type)
    # print(get_per_doc)
    # if document_type not in permitted_doctypes:
    #     frappe.throw("Access denied for the specified doctype.")

    if filters:
        condition = [
            f"(`tab{document_type}`.`name` like '%{filters}%') or (`tab{document_type}`.`customer` like '%{filters}%')"
        ]
    print(frappe.get_list(document_type))
    result = get_all(doctype=document_type, filters=condition, fields=fields,order_by="creation desc")
    count = len(result)

    if count == 0:
        success = 1
        msg = "No Records Found"
    else:
        total_pages = math.ceil(count / 10)
        page_no = min(int(page_no), total_pages)
        paginated_result = [result[i:i + 10] for i in range(0, count, 10)]
        data = paginated_result[page_no - 1]
        success = 1
        msg = "Records Found"
        total_count = count
    print(data)
    frappe.response["success"] = success
    frappe.response["message"] = msg
    frappe.response["data"] = data
    frappe.response["total_count"] = total_count

@frappe.whitelist(methods=["GET","POST","PUT"])
def get_sales_invoice_details(sales_invoice_id):
    success= 0
    msg = "Record Not Found"
    data=[]
    if sales_invoice_id and frappe.db.exists("Sales Invoice",sales_invoice_id):
        success= 1
        msg = "Record Found"
        # data = frappe.get_doc("Sales Invoice",sales_invoice_id)
        # print(data.as_dict())
        data = frappe.get_all("Sales Invoice",filters={"name":sales_invoice_id},fields=["name","customer","customer_name","tax_id","company","abbr","posting_date","posting_time","due_date","return_against","po_no","po_date","customer_address","billing_address_gstin","address_display","contact_person","contact_display","contact_mobile","contact_email","territory","shipping_address_name","customer_gstin","place_of_supply","shipping_address","company_address","company_gstin","company_address_display","dispatch_address_name","dispatch_address","currency","conversion_rate","selling_price_list","price_list_currency","plc_conversion_rate","set_warehouse","set_target_warehouse","total_billing_amount","total_billing_hours","total_qty","base_total","base_net_total","total_net_weight","total","net_total","taxes_and_charges","tax_category","other_charges_calculation","base_total_taxes_and_charges","total_taxes_and_charges","discount_amount","base_grand_total","base_rounding_adjustment","base_rounded_total","base_in_words","grand_total","rounding_adjustment","rounded_total","in_words","total_advance","outstanding_amount","disable_rounded_total","write_off_amount","base_write_off_amount","payment_terms_template","paid_amount","gst_category","status","customer_group","debit_to","party_account_currency","remarks","amount_eligible_for_commission","commission_rate","total_commission","from_date","to_date","against_income_account","ack_date","ack_no","distance","driver","driver_name","gst_transporter_id","gst_vehicle_type","invoice_copy","mode_of_transport","reverse_charge","transporter_name","vehicle_no"])[0]
        data["items"]=frappe.get_all("Sales Invoice Item",filters={"parent":sales_invoice_id},fields=["item_code","item_name","customer_item_code","description","gst_hsn_code","item_group","brand","image","qty","uom","rate","amount","base_rate","base_amount","pricing_rules","stock_uom_rate","net_rate","net_amount","base_net_rate","base_net_amount","taxable_value","income_account","expense_account","total_weight","weight_uom","warehouse","target_warehouse","batch_no","incoming_rate","serial_no","actual_qty","sales_order","so_detail","sales_invoice_item","delivery_note","delivered_qty"])
        data["payment_schedule"] = frappe.get_all("Payment Schedule",filters={"parent":sales_invoice_id},fields=["payment_term","description","due_date","mode_of_payment","invoice_portion","discount_type","discount_date","discount","payment_amount","outstanding","paid_amount","discounted_amount","base_payment_amount"])
    frappe.response["success"] = success
    frappe.response["message"] = msg
    frappe.response["sales_invoice_details"] = data

@frappe.whitelist(methods=["GET","POST","PUT"])
def get_transaction_approval_list(user_id,filters=None,page_no=1):
    document_type = "S4S Transaction Approval"
    fields = ["name as transaction_approval_id","cc_name as cc_name"]
    condition = None
    success, msg, data, total_count = 0, "Failed", [], 0
    # permitted_doctypes = get_user_permissions(user_id)
    # print(permitted_doctypes,type(permitted_doctypes["S4S CC List"][0]))
    # get_per_doc = get_allowed_docs_for_doctype(permitted_doctypes["S4S CC List"],document_type)
    # print(get_per_doc)
    # if document_type not in permitted_doctypes:
    #     frappe.throw("Access denied for the specified doctype.")

    if filters:
        condition = [
            f"(`tab{document_type}`.`name` like '%{filters}%') or (`tab{document_type}`.`cc_name` like '%{filters}%')"
        ]
    print(frappe.get_list(document_type))
    result = get_all(doctype=document_type, filters=condition, fields=fields,order_by="creation desc")
    count = len(result)

    if count == 0:
        success = 1
        msg = "No Records Found"
    else:
        total_pages = math.ceil(count / 10)
        page_no = min(int(page_no), total_pages)
        paginated_result = [result[i:i + 10] for i in range(0, count, 10)]
        data = paginated_result[page_no - 1]
        success = 1
        msg = "Records Found"
        total_count = count
    print(data)
    frappe.response["success"] = success
    frappe.response["message"] = msg
    frappe.response["data"] = data
    frappe.response["total_count"] = total_count

@frappe.whitelist(methods=["GET","POST","PUT"])
def get_transaction_approval_details(transaction_approval_id):
    success= 0
    msg = "Record Not Found"
    data=[]
    if transaction_approval_id and frappe.db.exists("S4S Transaction Approval",transaction_approval_id):
        success= 1
        msg = "Record Found"
        # data = frappe.get_doc("S4S Transaction Approval",transaction_approval_id)
        # print(data.as_dict())
        print()
        data = frappe.get_all("S4S Transaction Approval",filters={"name":transaction_approval_id},fields=["from_date","to_date","company","cc_name"])[0]
        data["approval_details"]=frappe.get_all("S4S Transaction Approval Item",filters={"parent":transaction_approval_id},fields=["date","cc_name","farmer_name","transaction_no","crop_name","qty","purchase_receipt","amount","total_deduction_amount","net_total","fpo_dc_no","fpo_dc_date","fpo_pi_no","fpo_pi_date","s4s_grn_no","s4s_grn_date","s4s_fpo_purchase_order","s4s_fpo_purchase_order_date","fpo_sale_order_no","fpo_sale_order_date","approver_name"])
    frappe.response["success"] = success
    frappe.response["message"] = msg
    frappe.response["transaction_approval_details"] = data