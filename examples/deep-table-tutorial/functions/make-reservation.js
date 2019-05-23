exports.handler = function(context, event, callback) {
    let moment = require('moment');
    let responseObject = {};

  let memory = JSON.parse(event.Memory);

  let first_name = memory.twilio.collected_data.make_reservation.answers.first_name.answer || '';
  let reservation_date = memory.twilio.collected_data.make_reservation.answers.date.answer || '';
  let reservation_time = moment(memory.twilio.collected_data.make_reservation.answers.time.answer, "hhmm").format("HH:mm a") || '';
  let party_size = memory.twilio.collected_data.make_reservation.answers.party_size.answer || '';

  console.log("First name: "+first_name );
  console.log("Reservation date: "+reservation_date);
  console.log("Reservation time: "+reservation_time);
  console.log("Party size: "+party_size);

  let message = "Ok "+first_name+". Your reservation for "+reservation_date+" at "+reservation_time+" for "+party_size+" people is now confirmed. thank you for booking with us";
  responseObject = {"actions":[
    { "say": { "speech": message } }
    ]};
    callback(null, responseObject);
};
