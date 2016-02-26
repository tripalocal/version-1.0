import React, { PropTypes } from 'react'
import {ModalContainer, ModalDialog} from 'react-modal-dialog'

const NewItemModal = ({ type, handleClose, handleSubmit }) => (
  <ModalContainer onClose={handleClose}>
    <ModalDialog onClose={handleClose}>
      <h3>New {type}</h3>
      <label forName="title">Title</label>
      <input name="title">
    </ModalDialog>
  </ModalContainer>
)

NewItemModal.propTypes = {
  type: PropTypes.func.string,
  handleClose: PropTypes.func.isRequired,
  handleSubmit: PropTypes.func.isRequired
}

export default NewItemModal
