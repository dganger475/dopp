import { registerComponent } from '@plasmicapp/host';
import MyButton from './components/MyButton';

export function registerAll() {
  registerComponent(MyButton, {
    name: 'MyButton',
    props: {
      children: 'slot'
    }
  });
}
