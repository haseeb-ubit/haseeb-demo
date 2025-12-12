///** @odoo-module **/
//
//odoo.define('elearning_colleges.college_website', function (require) {
//    'use strict';
//
//    var publicWidget = require('web.public.widget');
//
//    publicWidget.registry.CollegeResumeButton = publicWidget.Widget.extend({
//        selector: '.btn-resume',
//
//        start: function () {
//            var self = this;
//            this.$el.on('click', function(e) {
//                e.preventDefault();
//                var $btn = $(this);
//                var resumeId = $btn.data('resume-id');
//                var resumeType = $btn.data('resume-type');
//                var resumeIdEn = $btn.data('resume-id-en');
//
//                if (resumeId) {
//                    var resumeUrl = '';
//
//                    // If user has both resumes, prefer English, otherwise use the available one
//                    if (resumeType === 'both' && resumeIdEn) {
//                        // If both exist, show English by default
//                        resumeUrl = '/report/pdf/ust_resume_management.ust_resume_report_en/' + resumeIdEn;
//                    } else if (resumeType === 'ar' || resumeType === 'both') {
//                        // Arabic resume
//                        resumeUrl = '/report/pdf/ust_resume_management.ust_resume_report/' + resumeId;
//                    } else if (resumeType === 'en') {
//                        // English resume
//                        resumeUrl = '/report/pdf/ust_resume_management.ust_resume_report_en/' + resumeId;
//                    } else {
//                        // Default to Arabic
//                        resumeUrl = '/report/pdf/ust_resume_management.ust_resume_report/' + resumeId;
//                    }
//
//                    // Open resume PDF in new window
//                    window.open(resumeUrl, '_blank');
//                }
//                return false;
//            });
//            return this._super.apply(this, arguments);
//        },
//    });
//
//    return publicWidget.registry.CollegeResumeButton;
//});
//
