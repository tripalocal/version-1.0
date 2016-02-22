import './main.css!'
import 'react-select/dist/react-select.css!';
import React from 'react';
import ReactDOM from 'react-dom';
import App from './components/App.jsx!';

// TEST DATA
const DAYS = [
  {date: '2016-02-01', items: 'Lunching, Breathing, Rafting', transport: 'CX992', accommodation: 'Melbourne 4Star', restaurant: 'Continental breakfast'},
  {date: '2016-02-02', items: 'Eating, Breaking, Laughing', transport: 'Bus Ride', accommodation: 'Hilton 5star', restaurant: 'Great breakfast, lunch, dinner'},
  {date: '2016-02-03', items: 'Running, Jumping, Painting', transport: 'Airport transfer', accommodation: 'Cool Cottage', restaurant: ''},
];

ReactDOM.render(
  <App days={DAYS} />,
  document.getElementById('entry')
);

