import { expect } from 'chai'
import TestUtils from 'react-addons-test-utils'
import React from 'react'
import { App } from '../app/containers/App'

function setupApp(modalSetting) {
  let props = {
    showModal: modalSetting
  }
  let renderer = TestUtils.createRenderer()
  renderer.render(<App {...props} />)
  let output = renderer.getRenderOutput()

  return {
    props,
    output,
    renderer
  }
}

describe('Containers', () => {
  describe('App', () => {
    it('should render correctly', () => {
      const { output } = setupApp('NONE')
      expect(output.type).to.equal('div')
    })
    it('should not show modal if modal state is NONE', () => {
      const { output } = setupApp('NONE')
      expect(output.children).to.be.null
    })
  })
})
