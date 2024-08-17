!function() {
    class PaymentWidget extends HTMLElement {
        connectedCallback() {
            this.innerHTML = `
                <style>
                    payment-widget {
                        display: inline-block;
                    }
                    #payment-widget {
                        display: flex;
                        flex-direction: column;
                        align-items: center;
                        justify-content: space-between;
                        width: 300px;
                        height: 330px;
                        padding: 20px;
                        box-sizing: border-box;
                        opacity: 0;
                    }
                    #payment-title {
                        height: 50px;
                        display: flex;
                        align-items: center;
                    }
                    #payment-title h2 {
                        margin: 15px 0 0 0;
                        font-size: 20px;
                        color: #575757;
                    }
                    #payment-widget h3 {
                        margin: 0 0 0 0;
                        font-size: 18px;
                        color: #575757;
                    }
                    #payment-price h2{
                        margin: 5px 0 0 0;
                        font-size: 30px;
                        color: black;
                    }
                    #payment-price {
                        display: flex;
                        align-items: baseline;
                        margin-bottom: 10px;
                    }
                    #amount {
                        font-size: 30px;
                        color: black;
                    }
                    #payment-button {
                        display: inline-block;
                        padding: 10px 20px;
                        background-color: #0075d4;
                        color: white;
                        text-align: center;
                        cursor: pointer;
                        border-radius: 5px;
                        width: 80%;
                    }
                    #logo-container { /* Shadow effect */
                        box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
                        border-radius: 7px;
                        width: 130px;
                        height: 130px;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                    }
                    #logo {
                        max-width: 92%;
                        max-height: 92%;
                    }
                    h2, h3, #payment-button{
                        font-family: 'Verdana';
                        font-weight: 550;
                    }
                    #payment-name {
                        text-align: center;
                    }
                </style>
                <div id="payment-widget">
                    <div id="logo-container">
                        <img id="logo" src="logo.png" alt="Logo">
                    </div>
                    <div id="payment-title">
                        <h2 id="payment-name">
                        
                        </h2>
                    </div>
                    <div id="payment-price">
                        
                    </div>
                    <div id="payment-button"></div>
                </div>
            `;
            let planID = this.getAttribute('plan-id');
            let xhr = new XMLHttpRequest();
            xhr.open('POST', '/get_item');
            xhr.setRequestHeader('Content-Type', 'application/json');
            xhr.onload = function() {
                if (xhr.status === 200) {
                    let item = JSON.parse(xhr.responseText);
                    let itemName = item.name;
                    let itemPrice = item.price % 1 === 0 ? Math.round(item.price) : parseFloat(item.price).toFixed(2);
                    let recurring = item.recurring;
                    if (recurring != null) {
                        this.querySelector('#payment-price').innerHTML = '<h2>$' + itemPrice + '</h2><h3>/'+recurring+'</h3>';
                        this.querySelector('#payment-button').innerHTML = 'Subscribe';
                    } else {
                        this.querySelector('#payment-price').innerHTML = '<h2>$' + itemPrice + '</h2>';
                        this.querySelector('#payment-button').innerHTML = 'Purchase';
                    }
                    this.querySelector('#payment-name').innerHTML = itemName;
                    this.querySelector('#payment-widget').style.opacity = 1;
                } else {
                    console.error('Failed to get items.');
                }
            }.bind(this);
            xhr.send(JSON.stringify({planID: planID}));
            
            this.querySelector('#payment-button').addEventListener('click', () => {
                let cart = JSON.stringify(
                    { item: 'sub', planID: planID, quantity: 1},
                );
                sessionStorage.setItem('shoppingCart', cart);
                window.location.href = this.getAttribute('payment-url');
            });
        }
    }
    customElements.define('payment-widget', PaymentWidget);
}()