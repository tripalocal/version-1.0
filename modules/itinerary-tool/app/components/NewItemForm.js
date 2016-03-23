import React, { PropTypes } from 'react'
import { reduxForm } from 'redux-form'

let NewItemForm = ({ fields: { title, location, priceFixed, pricePP, description }, handleSubmit }) => (
  <form onSubmit={handleSubmit}>
    <label forName="title">Title</label>
    <input type="text" name="title" {...title} />

    <label forName="location">Location</label>
    <input type="text" name="location" {...location} />

    <label forName="priceFixed">Fixed Price</label>
    <input type="number" name="priceFixed" {...priceFixed} />

    <label forName="pricePP">Price per person</label>
    <input type="number" name="pricePP" {...pricePP} />

    <label forName="description">Description</label>
    <input type="text" name="description" {...description} />
    
    <input type="hidden" name="type" value="add" />

    <button type="submit">Submit</button>
  </form>
)

NewItemForm = reduxForm({
  form: 'newItem',
  fields: ['title', 'location', 'priceFixed', 'pricePP', 'description']
})(NewItemForm);

export default NewItemForm
