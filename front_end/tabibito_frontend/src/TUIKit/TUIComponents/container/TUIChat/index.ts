import TUIChatServer from './server';
import TUIChatComponent from './index.vue';

import Face from './plugin-components/face';
import Image from './plugin-components/image';
import Video from './plugin-components/video';
import File from './plugin-components/file';
import Forward from './plugin-components/forward';
import Words from './plugin-components/words';
import Evaluate from './plugin-components/evaluate';
import TypingHeader from './plugin-components/typingHeader';
import ReadReceiptDialog from './plugin-components/readReceiptDialog';
import Replies from './plugin-components/replies';
import Call from './plugin-components/call';
import ImagePreviewer from './plugin-components/imagePreviewer';
import MessageInput from './message-input/index';

let sendComponents: any = {
  Face,
  Image,
  Video,
  File,
  Evaluate,
  Words,
  Call,
};

export const messageComponents: any = {
  Forward,
};

export const otherComponents: any = {
  TypingHeader,
  ReadReceiptDialog,
  Replies,
  ImagePreviewer,
  MessageInput
};

export function getComponents(type: string) {
  let options: any = {};
  switch (type) {
    case 'send':
      options = sendComponents;
      break;
    case 'message':
      options = messageComponents;
      break;
    case 'other':
      options = otherComponents;
      break;
    default:
      break;
  }
  return options;
}

const install = (app: any) => {
  const components: any = { ...sendComponents, ...messageComponents, ...otherComponents };
  Object.keys(components).forEach((name: any) => {
    components[name].TUIServer = TUIChat.server;
  });
  TUIChatComponent.TUIServer = TUIChat.server;
  TUIChatComponent.components = { ...TUIChatComponent.components, ...components };
  app.component(TUIChat.name, TUIChatComponent);
};

const plugin = (TUICore: any) => {
  (TUIChat.server as any) = new TUIChatServer(TUICore);
  TUICore.component(TUIChat.name, TUIChat);
  return TUIChat;
};

const setPluginComponents = (Components: any) => {
  sendComponents = { ...sendComponents, ...Components };
};

const removePluginComponents = (nameList: Array<string>) => {
  nameList.map((name: string) => {
    delete sendComponents[name];
    return name;
  });
};

const TUIChat = {
  name: 'TUIChat',
  component: TUIChatComponent,
  server: TUIChatServer,
  sendComponents,
  messageComponents,
  otherComponents,
  install,
  plugin,
  setPluginComponents,
  removePluginComponents,
};

export default TUIChat;
