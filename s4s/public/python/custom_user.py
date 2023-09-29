import frappe
from frappe import _

@frappe.whitelist()
def fetch_data():
    print("running"*100)
    doc = frappe.get_all("User",filters={'enabled':1},fields=['name','mobile_no'])
    otp = frappe.get_doc("S4S OTP Verification")
    otp.users = []
    for i in doc:
        otp.append("users",{
            "user":i.name,
            "mobile_number":i.mobile_no
            # "timestamp":"0",
            # "otp":"0"
        })
    otp.save()
    otp.save()