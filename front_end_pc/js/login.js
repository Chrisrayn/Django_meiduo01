var vm = new Vue({
    el: '#app',
    data: {
        host,
        error_username: false,
        error_pwd: false,
        error_pwd_message: '请填写密码',
        username: '',
        password: '',
        remember: false
    },
    methods: {
        // 获取url路径?号后面的name值的参数
        // http://www.jd.com/login.html?a=200&next=www.boxuegu.com&b=200
        get_query_string: function(name){
            var reg = new RegExp('(^|&)' + name + '=([^&]*)(&|$)', 'i');
            var r = window.location.search.substr(1).match(reg);
            if (r != null) {
                return decodeURI(r[2]);
            }
            return null;
        },
        // 检查数据
        check_username: function(){
            if (!this.username) {
                this.error_username = true;
            } else {
                this.error_username = false;
            }
        },
        check_pwd: function(){
            if (!this.password) {
                this.error_pwd_message = '请填写密码';
                this.error_pwd = true;
            } else {
                this.error_pwd = false;
            }
        },
        // 表单提交
        on_submit: function(){
            // alert('xxx');
            this.check_username();
            this.check_pwd();

            if (this.error_username == false && this.error_pwd == false) {
                // alert('1111');
                axios.post(this.host+'/authorizations/', {
                        username: this.username,
                        password: this.password
                    }, {
                        responseType: 'json',
                    })
                    .then(response => {
                        // 使用浏览器本地存储保存token
                        if (this.remember) {
                            // 记住登录
                            sessionStorage.clear();
                            localStorage.token = response.data.token;
                            localStorage.user_id = response.data.user_id;
                            localStorage.username = response.data.username;
                        } else {
                            // 未记住登录
                            localStorage.clear();
                            sessionStorage.token = response.data.token;
                            sessionStorage.user_id = response.data.user_id;
                            sessionStorage.username = response.data.username;
                        }

                        // 跳转页面[当地址栏上面出现<next=地址>这样的路径时，登陆成功以后要跳转到指定的地址中]
                        var return_url = this.get_query_string('next');
                        if (!return_url) {
                            return_url = '/index.html';
                        }
                        location.href = return_url;
                    })
                    .catch(error => {
                        this.error_pwd_message = '用户名或密码错误';
                        this.error_pwd = true;
                    })
            }
        },
        // qq登录
        qq_login: function(){
            var state = this.get_query_string('next') || '/';
            axios.get(this.host + '/oauth/qq/authorization/?state=' + state, {
                    responseType: 'json'
                })
                .then(response => {
                    location.href = response.data.auth_url;
                })
                .catch(error => {
                    console.log(error.response.data);
                })
        }
    }
});