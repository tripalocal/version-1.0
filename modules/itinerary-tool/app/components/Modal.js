import React, { PropTypes } from 'react'
import {ModalContainer, ModalDialog} from 'react-modal-dialog'
import NewItemForm from './NewItemForm'
import AssignHostForm from './AssignHostForm'

const Modal = ({setting, handleClose, handleSubmit }) => (
  <ModalContainer onClose={handleClose}>
    <ModalDialog onClose={handleClose}>
      {(() => {
        switch(setting) {
          case 'NEW_ITEM':
            return <NewItemForm handleSubmit={handleSubmit} />
            case 'ASSIGN_HOST':
              return <AssignHostForm handleSubmit={handleSubmit} />
              default: return
        }
      })()}
    </ModalDialog>
  </ModalContainer>
)


Modal.propTypes = {
  type: PropTypes.string,
  handleClose: PropTypes.func,
  handleSubmit: PropTypes.func
}

export default Modal
