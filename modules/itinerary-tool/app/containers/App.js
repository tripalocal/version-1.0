import React from 'react'
import { connect } from 'react-redux'
import TopBar from './TopBar'
import SideBar from './SideBar'
import TableState from './TableState'
import ModalState from './ModalState'

export const App = ({ showModal }) => (
  <div>
    <TopBar />
    <SideBar />
    <TableState />
    { showModal !== 'NONE'
      ? <ModalState />
      : null }
  </div>
)

const mapStateToProps = (state) => {
  return { showModal: state.modal['display'] }
}

export default connect(mapStateToProps)(App)

