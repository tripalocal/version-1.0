import React, { PropTypes } from 'react'
import {ModalContainer, ModalDialog} from 'react-modal-dialog'
import NewItemForm from './NewItemForm'
import AssignHostForm from './AssignHostForm'
import ChooseCityForm from './ChooseCityForm'

const Modal = ({date, setting, handleClose}) => (
  <ModalContainer onClose={handleClose}>
    <ModalDialog onClose={handleClose}>
    {(() => {
      switch (setting) {
        case 'NEW_ITEM':
          return <NewItemForm />
        case 'ASSIGN_HOST':
          return <AssignHostForm />
        case 'CHOOSE_CITY':
          return <ChooseCityForm date={date} />
      }
    })()}
    </ModalDialog>
  </ModalContainer>
)

Modal.propTypes = {
  setting: PropTypes.string,
  handleClose: PropTypes.func,
}

export default Modal
