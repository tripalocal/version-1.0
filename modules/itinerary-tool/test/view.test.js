import { expect } from 'chai'
import TestUtils from 'react-addons-test-utils'
import sd from 'skin-deep'
import React from 'react'
import Table from '../app/components/Table'

describe('Empty test', () => {
  it('should run successfully', () => {
    expect('A').to.equal('A') 
  })
})

describe('Table component', () => {
  const testDates = {
    2016-03-01: {
      city: 'melbourne',
      experiences: {
        items: ['cool activity', 'another one'],
        host: '',
        display: 'NORMAL'
      },
      transport: {
        items: [],
        host: 'Guy',
        display: 'NORMAL'
      },
      accommodation: {
        items: ['Hilton']
        host: 'Guy'
        display: NORMAL
      },
      restaurants: {
        items: ['Food Inc.'],
        host: 'Person',
        display: 'EDIT'
      }
    },
    2016-03-02: {
      city: 'melbourne',
      experiences: {
        items: ['cool activity', 'another one'],
        host: '',
        display: 'NORMAL'
      },
      transport: {
        items: [],
        host: 'Guy',
        display: 'NORMAL'
      },
      accommodation: {
        items: ['Hilton']
        host: 'Guy'
        display: NORMAL
      },
      restaurants: {
        items: ['Food Inc.'],
        host: 'Person',
        display: 'EDIT'
      }
    }
  }

  it('should render table headings', () => {
    tree = sd.shallowRender(React.createElement(Table, {dates: testDates}))
    expect(tree.subTree('th')[0].text()).to.equal('Date')
  })
})
