import { expect } from 'chai'
import TestUtils from 'react-addons-test-utils'
import { isComponentOfType, findAllWithType } from 'react-shallow-testutils'
import React from 'react'
import Table from '../app/components/Table'
import Row from '../app/components/Row'
import Modal from '../app/components/Modal'
import AssignHostForm from '../app/components/AssignHostForm'
import NewItemForm from '../app/components/NewItemForm'
import { ModalContainer, ModalDialog } from 'react-modal-dialog'

function setupTable() {
  let props = {
  dates: {
    '2016-03-01': {
      city: 'melbourne',
      experiences: {
        items: [{title: 'great activity', id: 1205}, {title: 'another great one', id:14902}],
        host: '',
        display: 'NORMAL'
      },
      transport: {
        items: [],
        host: 'Guy',
        display: 'NORMAL'
      },
      accommodation: {
        items: ['Hilton'],
        host: 'Guy',
        display: 'NORMAL'
      },
      restaurants: {
        items: ['Food Inc.'],
        host: 'Person',
        display: 'NORMAL'
      }
    },
    '2016-03-02': {
      city: 'melbourne',
      experiences: {
        items: [{title: 'cool activity', id: 54950}, {title: 'another one', id: 54135}],
        host: '',
        display: 'NORMAL'
      },
      transport: {
        items: [],
        host: 'Guy',
        display: 'NORMAL'
      },
      accommodation: {
        items: ['Hilton'],
        host: 'Guy',
        display: 'NORMAL'
      },
      restaurants: {
        items: [{title: 'Food Inc.', id: 12345}],
        host: 'Person',
        display: 'NORMAL'
      }
    }
  }
}
  let renderer = TestUtils.createRenderer()
  renderer.render(<Table {...props} />)
  let output = renderer.getRenderOutput()

  return {
    props,
    output,
    renderer
  }
}

function setupModal(setting) {
  let props = {
    setting: setting,
    handleClose: null,
    handleSubmit: null 
  }
  let renderer = TestUtils.createRenderer()
  renderer.render(<Modal {...props} />)
  let output = renderer.getRenderOutput()

  return {
    props,
    output,
    renderer
  }
}

function setupRow() {
  const props = {
    date: '2016-03-01',
    fields: {
      city: 'Melbourne',
      experiences: {},
      transport: {},
      accommodation: {},
      restaurants: {}
    }
  }
  let renderer = TestUtils.createRenderer()
  renderer.render(<Row {...props} />)
  let output = renderer.getRenderOutput()

  return {
    props,
    output,
    renderer
  }
}

describe('Components', () => {
  describe('table', () => {
    it('should render correctly', () => {
      const { output } = setupTable()

      expect(output.type).to.equal('table')
      expect(output.props.className).to.equal('table')

      let [ thead, tbody ] = output.props.children
      expect(thead.type).to.equal('thead')
      expect(tbody.type).to.equal('tbody')
    })
    
  })

  describe('row', () => {
    it('should render correctly', () => {
      const { output } = setupRow()
      
      expect(output.type).to.equal('tr')
      expect(output.props.children[0].type).to.equal('td')
    })
    it('should render a column for each field', () => {
      const { output } = setupRow()
      let columns = output.props.children
      expect(columns[0].props.children).to.equal('2016-03-01')
      expect(columns).to.have.lengthOf(6)
    })
  })

  describe('modal', () => {
    it('should render NewItemForm if setting is NEW_ITEM', () => {
      const { output } = setupModal('NEW_ITEM')
      expect(findAllWithType(output, NewItemForm)).to.have.lengthOf(1)
    })

    it('should render AssignHostForm if setting is ASSIGN_HOST', () => {
      const { output } = setupModal('ASSIGN_HOST')
      expect(isComponentOfType(output, ModalContainer)).to.be.true
      expect(findAllWithType(output, AssignHostForm)).to.have.lengthOf(1)
    })
  })
})
