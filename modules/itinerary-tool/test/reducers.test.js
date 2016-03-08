import { expect } from 'chai'
import reducer from '../app/reducers.js'

describe('Reducers', () => {
  describe('modal', () => {
    it('should return the initial state', () => {
      expect(
        reducer(undefined, {})
      ).to.eql(
        {
          modal: 'NONE',
          dates: {},
          form: {} 
        }
      )
    })

    it('should handle SHOW_MODAL', () => {
      expect(
        reducer({}, {
          type: 'SHOW_MODAL',
          setting: 'NEW_ITEM'
        })
      ).to.eql(
        {
        modal: 'NEW_ITEM',
        dates: {},
        form: {}
        }
      )
    })
  })

  describe('dates', () => {
    it('should return the initial state', () => {

    })

    it('should handle SHOW_SELECT', () => {

    })
  })
})
