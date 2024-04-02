<script>
var stripe = Stripe("{{ STRIPE_PUBLIC_KEY }}");
var elements = stripe.elements();

var form = document.getElementById("paymentForm");
var stripeForm = document.getElementById("stripeCardForm")
var loader = document.getElementById("loader");

var cardOptionSelect = document.getElementById('cardOptions');

function getSelectedCardOptionValue() {
    return cardOptionSelect.options[cardOptionSelect.selectedIndex].value;
}

function toggleStripeForm(selectedCardOptionValue) {
    if (selectedCardOptionValue === "newCard") {
        stripeForm.style.display = "block";
    } else {
        stripeForm.style.display = "none";
    }
}

var selectedCardOptionValue = getSelectedCardOptionValue();
toggleStripeForm(selectedCardOptionValue);

cardOptionSelect.addEventListener("change", e => {
    toggleStripeForm(e.target.value)
})

function toggleLoader(status) { 
  var display = status ? "block" : "none";
  loader.style.display = display
}

// Set up Stripe.js and Elements to use in checkout form
var style = {
  base: {
    color: "#32325d",
  }
};

var card = elements.create("card", { style: style });
card.mount("#card-element");

card.on('change', function(event) {
  var displayError = document.getElementById('card-errors');
  if (event.error) {
    displayError.textContent = event.error.message;
  } else {
    displayError.textContent = '';
  }
});

document.getElementById("paymentForm").addEventListener("submit", e => {
    e.preventDefault();
    toggleLoader(true);

    var selectedCardOptionValue = getSelectedCardOptionValue();
    var selectedCard = card;
    if (selectedCardOptionValue != "newCard") {
        form.submit()
    } else {
        stripe.confirmCardPayment("{{ client_secret }}", {
            payment_method: {
                card: card,
            },
            setup_future_usage: 'off_session'
        })
        .then(function(result) {
            toggleLoader(false);
            if (result.error) {
                // Show error to your customer
                console.log(result.error.message);
            } else {
                if (result.paymentIntent.status === 'succeeded') {
                // Show a success message to your customer
                // There's a risk of the customer closing the window before callback execution
                // Set up a webhook or plugin to listen for the payment_intent.succeeded event
                // to save the card to a Customer

                // The PaymentMethod ID can be found on result.paymentIntent.payment_method
                    form.submit()
                }
            }
        });
    }

    

})


</script>

<script src="https://www.paypal.com/sdk/js?client-id={{ PAYPAL_CLIENT_ID }}">
</script>

<script>

    const loader = document.getElementById('loader');
    const paymentInfo = document.getElementById('paymentInfo');

    function toggleLoader(on) {
        loader.style.display = on === true ? "block" : "none";
        paymentInfo.style.display = on === true ? "none" : "block";
    }

    function getCookie(name) {
        var cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            var cookies = document.cookie.split(';');
            for (var i = 0; i < cookies.length; i++) {
                var cookie = cookies[i].trim();
                // Does this cookie string begin with the name we want?
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
    var csrftoken = getCookie('csrftoken');

    function sendOrderConfirmed(details) {
        return fetch("{% url 'cart:confirm-order' %}", {
            method: "post",
            body: JSON.stringify(details),
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": csrftoken
            }
        })
    }

    paypal.Buttons({
        createOrder: function (data, actions) {
            return actions.order.create({
                purchase_units: [{
                    amount: {
                        value: '{{ order.get_total }}'
                    }
                }]
            });
        },
        onApprove: function (data, actions) {
            toggleLoader(true);
            // This function captures the funds from the transaction.
            return actions.order.capture().then(function (details) {
                // This function shows a transaction success message to your buyer.
                sendOrderConfirmed(details).then(res => {
                    toggleLoader(false);
                    const alertSuccess = document.getElementById('alertSuccess');
                    alertSuccess.style.display = 'block';
                    setTimeout(function () {
                        window.location.replace("{{ CALLBACK_URL }}")
                    }, 3000);
                })
            })
                .catch(err => {
                    const alertFailure = document.getElementById('alertFailure');
                    alertFailure.style.display = 'block';
                })
                .finally(() => toggleLoader(false));
        }
    }).render('#paypal-button-container');
</script>


