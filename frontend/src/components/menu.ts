import { Menus } from '@/types/menu';

export const menuData: Menus[] = [
    {
        id: '1',
        title: 'ArtiScope Generator',
        index: '1',
        icon: 'HomeFilled',
        children: [
            {
                id: '11',
                pid: '1',
                index: '/text-to-image',
                title: '文生图',
            },
            {
                id: '12',
                pid: '1',
                index: '/image-to-image',
                title: '图片转换',
            },
            {
                id: '13',
                pid: '1',
                index: '/video-to-video',
                title: '视频转换',
            },
        ],
    },
];
