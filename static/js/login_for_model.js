$("#login_medal_form").submit(function(event){
            event.preventDefault();
            $.ajax({
                url: 'login_for_medal/',
                type: 'POST',
                data: $(this).serialize(),
                cache: false,
                success: function(data){
                    if(data['status']=='SUCCESS'){
                        window.location.reload();
                    }else{
                        $('#login_medal_tip').text('用户名或密码不正确');
                    }
                }
            });
        });