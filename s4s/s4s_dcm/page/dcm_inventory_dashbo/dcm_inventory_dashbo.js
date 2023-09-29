

frappe.pages['dcm-inventory-dashbo'].on_page_load = function(wrapper) {
    new ReportPage(wrapper);
}



ReportPage = Class.extend({
    init:function(wrapper){
        this.page = frappe.ui.make_app_page({
            parent: wrapper,
            single_column: true

        })
        let link = `https://analytics.mannlowe.com:8088/superset/dashboard/35/?warehouse_type=DCM&preselect_filters=%7B%7D&standalone=true&native_filters_key=rGFldejrLYUnrpFVv0wHR-G2owhgORgTiJv8KtmC1cICoLqN8GOtxySVWoAyqKkd`

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

const myLink = document.querySelector('.navbar-brand.navbar-home');
myLink.addEventListener('click', function() {
	frappe.set_route('app', 'home');
	window.location.reload()
});


