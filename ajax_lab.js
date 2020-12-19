function ajax_lab(){
    //pythonに送信するjsonの形を指定。ここでは({"なんとなく":idがselect_lab_idのタグのフォームの値})。工夫すれば複数データ送信可能。
    var lab_json = JSON.stringify({"lab":$('#lab_select_name').val()});
    $.ajax({
      type: 'POST',
      url: '/ajax_lab',
      data: lab_json,
      contentType: 'application/json',
      success:
        function (data){
          //↓ここからajax(非同期通信)の処理
          console.log("ajax_lab()のdataまるごと"+data);
          $('#year_select_id').children().remove();//まずは、id="select_year_id"の子要素を全部削除

          var arr = data;//pythonのajax処理後のデータをarrに格納
          for(var i=0;i<arr.length;i++){
            let op = document.createElement("option");//変数opにoption要素を作る動作をしこむ。発動はしない。
            op.value = arr[i].year;
            op.text = arr[i].year;//.valueでoptionタグのvalue=""を設定。data = arr = [{},{},...]なので、[i]番目で指定、その後.キー名で値を取り出す。
            //op.text = arr[i].year;//.textでoptionタグの間に挟む表示名を設定。表示名。
            document.getElementById("year_select_id").append(op);//id="select_year_id"のあるタグの中にさっきの仕込んだ動作をぶちかまし発動。
          }
          //↑ここまで
        }
    })
  }
  