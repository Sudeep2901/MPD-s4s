

frappe.pages['dcm-dashboard'].on_page_load = function(wrapper) {
    new ReportPage(wrapper);
}

ReportPage = Class.extend({
    init:function(wrapper){
        
        this.page = frappe.ui.make_app_page({
            parent: wrapper,
            single_column: true

        })
        let link = `https://analytics.mannlowe.com:8088/superset/dashboard/34/?user=${frappe.session.user}&standalone=true&native_filters_key=5RjFeRHKwSj5-FlBecdlLIV4Y3S7yokYL2QL_9XhFQM4YJU3LOn-IAxJhJAJBg5G`

        $("div").remove('.page-head.flex');
        $("div").remove('.page-head.flex.drop-shadow');
        $("div").remove('.row.layout-main');
        let body = `
            <div class="page-form">
                <iframe
                    src=${link}
                    frameborder="0"
                    width="100%"
                    height="867"
                    allowtransparency
                ></iframe>
            </div>

        `
        $(wrapper).append(body);

    },

  

})

const myLink1 = document.querySelector('.navbar-brand.navbar-home');
myLink1.addEventListener('click', function() {
    frappe.set_route('app', 'home');
    window.location.reload() 
});

