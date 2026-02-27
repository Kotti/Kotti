// JSLint options:
/*global $, angular, document, qq*/

"use strict";
var app = angular.module('kotti', []);

// copied from https://gist.github.com/thomseddon/3511330
app.filter('bytes', function () {
    return function (bytes, precision) {

        if (isNaN(parseFloat(bytes)) || !isFinite(bytes)) {
            return '-';
        }
        if (typeof precision === 'undefined') {
            precision = 1;
        }

        var units = ['bytes', 'kB', 'MB', 'GB', 'TB', 'PB'],
            number = Math.floor(Math.log(bytes) / Math.log(1024));
        if (!isFinite(number)) {
            number = 0;
        }

        return (bytes / Math.pow(1024, Math.floor(number))).toFixed(precision) + ' ' + units[number];
    };
});

function UploadController($scope, $http, $log) {

    $log.info("Initializing UploadController...");

    $scope.files = [];
    $scope.errors = [];
    $scope.numFilesWaiting = 0;

    $scope.uploadAll = function () {
        $scope.uploader.uploadStoredFiles();
    };

    $scope.dismissError = function (file) {
        $scope.errors.splice($scope.errors.indexOf(file), 1);
    };

    $scope.apply = function (fn) {
        var phase = this.$root.$$phase;
        if (phase === '$apply' || phase === '$digest') {
            if (fn && (typeof (fn) === 'function')) {
                fn();
            }
        } else {
            this.$apply(fn);
        }
    };

    $scope.uploader = new qq.FineUploaderBasic({
        debug: true,
        autoUpload: false,
        button: $('#btn-select-files')[0],
        element: document.getElementById('uploader'),
        request: {
            endpoint: null
        },
        callbacks: {
            //onValidate: function (fileOrBlobData) {
            onValidate: function () {
                $log.info("onValidate");
            },
            onSubmit: function (id, name) {
                $log.info("onSubmit");
                $scope.apply(function () {
                    var file = $scope.uploader.getFile(id);
                    $http.get(
                        $scope.endpoints.content_types,
                        {params: {mimetype: file.type}}
                    //).success(function (data, status, headers, config) {
                    ).success(function (data) {
                        var contentTypes = data.content_types,
                            file = {
                                id: id,
                                name: name,
                                size: $scope.uploader.getSize(id),
                                file: $scope.uploader.getFile(id)
                            };

                        if (contentTypes.length === 0) {
                            // todo: display meaningful error message
                            file.status = 'Error';
                            file.error = 'There is no content type in this context that knows create items from that file type.';
                            $scope.errors.splice(id, 0, file);
                            return false;
                        }

                        file.status = 'ready for upload';
                        file.transfered = {bytes: 0, percent: 0};
                        file.allowedTypes = contentTypes;
                        file.desiredType = contentTypes[0];

                        $scope.files.splice(id, 0, file);
                        $scope.numFilesWaiting += 1;
                    });
                });
            },
            //onUpload: function (id, name) {
            onUpload: function (id) {
                $log.info("onUpload");
                $scope.apply(function () {
                    $scope.files[id].status = 'uploading';
                    $scope.uploader.setParams({
                        content_type: $scope.files[id].desiredType.name
                    }, id);
                    $scope.numFilesWaiting -= 1;
                });
            },
            onProgress: function (id, name, uploadedBytes, totalBytes) {
                $scope.apply(function () {
                    $scope.files[id].transfered.bytes = uploadedBytes;
                    $scope.files[id].transfered.percent = Math.round(uploadedBytes / totalBytes * 100);
                });
            },
            //onCancel: function (id, name) {
            onCancel: function (id) {
                $log.info("onCancel");
                $scope.apply(function () {
                    $scope.files[id].status = 'cancelled';
                });
            },
            //onError: function (id, name, errorReason) {
            onError: function (id) {
                $log.info("onError");
                $scope.apply(function () {
                    $scope.files[id].status = 'failed';
                });
                return false;
            },
            onComplete: function (id, name, response) {
                $log.info("onComplete");
                // debugger;
                $scope.apply(function () {
                    if ($scope.files[id].status === 'uploading') {
                        $scope.files[id].status = 'complete';
                        $scope.files[id].url = response.url;
                    }
                });
            }
        }
    });

    $scope.$watch('endpoints', function (endpoints) {
        $scope.uploader.setEndpoint(endpoints.upload);
    });

    $log.info("UploadController initialized.");
}
