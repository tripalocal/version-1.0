import { expect } from 'chai'
import * as actions from '../app/actions'

describe('Actions', () => {
  it('should create an action SHOW_MODAL', () => {
    const date = '2016-03-09'
    const field = 'restaurant'
    const setting = 'NEW_ITEM'
    const expectedAction = {
      type: 'SHOW_MODAL',
      date,
      field,
      setting
    }
    expect(actions.showModal(date, field, setting)).to.eql(expectedAction)
  })

  it('should create an action SHOW_SELECT', () => {
    const date = '2016-03-09'
    const field = 'restaurant'
    const setting = 'EDIT'
    const expectedAction = {
      type: 'SHOW_SELECT',
      date,
      field,
      setting
    }
    expect(actions.showSelect(date, field, setting)).to.eql(expectedAction)
  })

  it('should create an action ADD_DATE', () => {
    const date = '2016-03-09'
    const expectedActionBefore = {
      type: 'ADD_DATE',
      date: '2016-03-08'
    }
    const expectedActionAfter = {
      type: 'ADD_DATE',
      date: '2016-03-10'
    }
    expect(actions.addDate(date, city, 'BEFORE')).to.eql(expectedActionBefore)
    expect(actions.addDate(date, city, 'AFTER')).to.eql(expectedActionAfter)
  })

  it('should create an action REMOVE_DATE', () => {
    const date = '2016-03-09'
    const expectedAction = {
      type: 'REMOVE_DATE',
      date
    }
    expect(actions.removeDate(date)).to.eql(expectedAction)
  })

  it('should create an action MOVE_DATE', () => {
    const date = '2016-03-09'
    const expectedActionBack = {
      type: 'MOVE_DATE',
      oldDate: '2016-03-09',
      newDate: '2016-03-08'
    }
    const expectedActionForward = {
      type: 'MOVE_DATE',
      oldDate: '2016-03-09',
      newDate: '2016-03-10'
    }
    expect(actions.moveDate(date, 'BACK')).to.eql(expectedActionBack)
    expect(actions.moveDate(date, 'FORWARD')).to.eql(expectedActionForward)
  })
})
