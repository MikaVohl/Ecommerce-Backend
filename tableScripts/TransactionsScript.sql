/****** Object:  Table [dbo].[Transactions]    Script Date: 2024-06-25 12:29:02 PM ******/
SET ANSI_NULLS ON
GO

SET QUOTED_IDENTIFIER ON
GO

CREATE TABLE [dbo].[Transactions](
	[traID] [int] IDENTITY(1,1) NOT NULL,
	[traTimestamp] [datetime] NOT NULL,
	[traAmount] [money] NOT NULL,
	[traCustID] [int] NOT NULL,
	[traDesc] [varchar](22) NULL,
	[traSuccess] [bit] NOT NULL
) ON [PRIMARY]
GO

