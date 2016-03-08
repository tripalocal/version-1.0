import React, { PropTypes } from 'react'
import {ModalContainer, ModalDialog} from 'react-modal-dialog'
import NewItemForm from './NewItemForm'
import AssignHostForm from './AssignHostForm'

const Modal = ({setting, handleClose, handleSubmit }) => (
  <ModalContainer onClose={handleClose}>
    <ModalDialog onClose={handleClose}>
      {setting === 'NEW_ITEM'
        ? <NewItemForm handleSubmit={handleSubmit} />
        : <AssignHostForm handleSubmit={handleSubmit} />}
    </ModalDialog>
  </ModalContainer>
)


Modal.propTypes = {
  type: PropTypes.string,
  handleClose: PropTypes.func,
  handleSubmit: PropTypes.func
}

export default Modal
