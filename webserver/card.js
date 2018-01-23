function streamData() {

    // setup websocket with callbacks
    var ws = new WebSocket('ws://localhost:8080/');
    //var ws = new ReconnectingWebSocket('ws://localhost:8080/');
    
    ws.onopen = function() {
        console.log('connect');
    };

    ws.onclose = function() {
        console.log('disconnect');
    };

    ws.onmessage = function(e) {
        data = e.data.trim();
        console.log(data)
        receivedData(data);
    };
}

function receivedData(data) {
    var d = data.split(",");
    createCard(d[1], d[0]);
    // Object.each(data, function(title, img_base64_str) {
    //     // var timeSeries = allTimeSeries[name];
    //     // if (timeSeries) {
    //     //     timeSeries.append(Date.now(), value);
    //     //     allValueLabels[name].text(value);
    //     // }
    // });
}

function createCard(title, img_base64_str) {
    var img = "url('data:image/png;base64, "+ img_base64_str + "')";
    var time_stamp = Date();
    var new_card = [
        `<div class="item">`,
        `<a class="card">`,
        `<div class="thumb" style="background-image: ${img};background-size: cover;"></div>`,
        `<article>`,
        `<h1>Animal detected: ${title}</h1>`,
        `<p>${time_stamp}</p>`,
        `</article>`,
        `</a>`,
        `</div>`
      ].join(' ');

    var new_card_div = document.createElement( 'div' );
    new_card_div.innerHTML = new_card
    document.getElementById("band").appendChild(new_card_div);
}

$(function() {
    streamData();
});